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
        """
        Calculate option price using Black-Scholes formula
        
        Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Implied volatility
        option_type: 'call' or 'put'
        
        Returns:
        Option price
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put option
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        return price
    def calculate_time_to_expiration(self, current_time, expiration_date, market_close=time(15, 0)):
        """
        Calculate time to expiration in years
        
        Parameters:
        current_time: Current datetime
        expiration_date: Option expiration date
        market_close: Market closing time (default: 3:00 PM Central Time)
        
        Returns:
        Time to expiration in years
        """
        # Convert to central time
        central = pytz.timezone('US/Central')
        current_time = current_time.astimezone(central)
        
        # Create datetime for expiration at market close
        expiration_datetime = datetime.combine(expiration_date, market_close)
        expiration_datetime = central.localize(expiration_datetime)
        
        # Calculate time difference in days
        time_diff = (expiration_datetime - current_time).total_seconds() / (365.25 * 24 * 60 * 60)
        return max(time_diff, 0)  # Ensure non-negative value
    def process_option_data(self, option_data, current_time=None):
        """
        Process streaming option data
        
        Parameters:
        option_data: DataFrame containing option data (strike, IV, type, expiration_date, etc.)
        current_time: Current time (default: now)
        
        Returns:
        DataFrame with option data and calculated Black-Scholes prices
        """
        if current_time is None:
            current_time = datetime.now(pytz.utc)
        
        # Market closing time (3 PM Central)
        market_close = time(15, 0)
        
        # Calculate Black-Scholes price for each option
        option_data['BS_Price'] = option_data.apply(
            lambda row: self.black_scholes(
                S=row['underlying_price'],
                K=row['strike'],
                T=self.calculate_time_to_expiration(current_time, row['expiration_date'], market_close),
                # r=row['risk_free_rate'],
                r = 0,
                sigma=row['IV'],
                option_type=row['option_type']
            ), axis=1
        )
        
        return option_data
    def analyze(self, option_data):
        """
        Analyze the option data and return the results
        """