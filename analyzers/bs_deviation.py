from analyzers.base import BaseAnalyzer
import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import datetime, time, timedelta
import pytz
from models import SPXOptionStream, db

class BSDeviationAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    def black_scholes(self, S, K, T, sigma, r=0, option_type='call'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type.lower() == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    def calculate_time_to_expiration(self, current_time, expiration_date, market_close=time(15, 0)):
        central = pytz.timezone('US/Central')
        current_time = current_time.astimezone(central)
        expiration_datetime = datetime.combine(expiration_date, market_close)
        expiration_datetime = central.localize(expiration_datetime)
        time_diff = (expiration_datetime - current_time).total_seconds() / (365.25 * 24 * 60 * 60)
        return max(time_diff, 0)

    def process_option_data(self, option_data, current_time=None):
        if current_time is None:
            current_time = datetime.now(pytz.utc)

        market_close = time(15, 0)

        option_data['BS_Price'] = option_data.apply(
            lambda row: self.black_scholes(
                S=row['underlying_price'],
                K=row['strike'],
                T=self.calculate_time_to_expiration(current_time, row['expiration_date'], market_close),
                r=0,
                sigma=row['IV'],
                option_type=row['option_type']
            ), axis=1
        )

        return option_data

    def analyze(self):

        session = db.session
        # Get the latest timestamp
        latest_timestamp = session.query(SPXOptionStream.timestamp)\
                                  .order_by(SPXOptionStream.timestamp.desc())\
                                  .first()

        if not latest_timestamp:
            return []

        latest_time = latest_timestamp[0]

        # Query latest records
        records = session.query(SPXOptionStream).filter_by(timestamp=latest_time).all()
        if not records:
            return []

        # Transform to long format: each row = one option (call or put)
        rows = []
        for r in records:
            # Skip if IV is missing or zero
            if r.call_iv:
                rows.append({
                    'strike': r.strike_price,
                    'IV': r.call_iv,
                    'option_type': 'call',
                    'expiration_date': r.exp_date,
                    'underlying_price': self.get_underlying_price(),  # You must define this
                    'market_price': (r.call_bid + r.call_ask) / 2 if r.call_bid and r.call_ask else r.call_last,
                })
            if r.put_iv:
                rows.append({
                    'strike': r.strike_price,
                    'IV': r.put_iv,
                    'option_type': 'put',
                    'expiration_date': r.exp_date,
                    'underlying_price': self.get_underlying_price(),  # You must define this
                    'market_price': (r.put_bid + r.put_ask) / 2 if r.put_bid and r.put_ask else r.put_last,
                })

        df = pd.DataFrame(rows)
        if df.empty:
            return []

        df = self.process_option_data(df)
        df['Deviation'] = df['market_price'] - df['BS_Price']
        df['Percent_Deviation'] = (df['Deviation'] / df['BS_Price']) * 100
        df = df.sort_values(by='Percent_Deviation', ascending=False)

        return df.to_dict(orient='records')

    def get_underlying_price(self):
        spot = db.session.execute(
            db.select(SPXOptionStream)
            .order_by(SPXOptionStream.timestamp.desc())
            .limit(1)
        ).scalar()
        underlying_price = spot.strike_price if spot else None
        return underlying_price