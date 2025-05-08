from analyzers.base import BaseAnalyzer
from datetime import datetime
import numpy as np
from scipy.stats import linregress

class SkewAnalyzer(BaseAnalyzer):
    name = "skew"
    description = "IV Skew Analyzer"
    refresh_interval = 120  # seconds

    def analyze(self, market_data):
        if not market_data or not market_data.get('expirations'):
            return {
                'timestamp': datetime.now().isoformat(),
                'error': 'No market data available',
                'skew_data': {}
            }

        skew_results = {}
        for expiry, data in market_data['expirations'].items():
            puts = [o for o in data['puts'] if o.get('iv')]
            calls = [o for o in data['calls'] if o.get('iv')]
            
            if not puts or not calls:
                continue

            # Calculate put skew (slope of IV vs. strike)
            put_strikes = [o['strike'] for o in puts]
            put_ivs = [o['iv'] for o in puts]
            put_slope = linregress(put_strikes, put_ivs).slope if len(put_strikes) > 1 else 0

            # Calculate call skew
            call_strikes = [o['strike'] for o in calls]
            call_ivs = [o['iv'] for o in calls]
            call_slope = linregress(call_strikes, call_ivs).slope if len(call_strikes) > 1 else 0

            skew_results[expiry] = {
                'put_slope': put_slope,
                'call_slope': call_slope,
                'skew_ratio': put_slope / call_slope if call_slope else float('inf'),
                'put_count': len(puts),
                'call_count': len(calls)
            }

        return {
            'timestamp': datetime.now().isoformat(),
            'skew_data': skew_results,
            'primary_expiry': market_data['primary_expiry']
        }