from analyzers.base import BaseAnalyzer
import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import datetime, time
import pytz

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

    def analyze(self, option_data):
        df = self.process_option_data(option_data)

        df['Deviation'] = df['market_price'] - df['BS_Price']
        df['Percent_Deviation'] = (df['Deviation'] / df['BS_Price']) * 100
        df = df.sort_values(by='Percent_Deviation', ascending=False)

        return df.to_dict(orient='records')
    def fetch_market_data(self):
        return 0