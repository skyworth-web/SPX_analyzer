from .base import BaseAnalyzer
from datetime import datetime
import numpy as np

class SpreadAnalyzer(BaseAnalyzer):
    name = "spread"
    description = "SPX Credit Spread Analyzer"
    refresh_interval = 15  # seconds
    
    def analyze(self, market_data):
        """Calculate spread metrics"""
        if not market_data or not market_data.get('expirations'):
            return {
                'timestamp': datetime.now().isoformat(),
                'error': 'No option chain data available',
                'put_spreads': [],
                'call_spreads': [],
                'summary': self._empty_summary()
            }
            
        primary_expiry = market_data['primary_expiry']
        expiration_data = market_data['expirations'][primary_expiry]
        
        put_spreads = self._calculate_spreads(expiration_data['puts'], 'put')
        call_spreads = self._calculate_spreads(expiration_data['calls'], 'call')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'spot_price': market_data['spot_price'],
            'expiry': primary_expiry.isoformat(),
            'put_spreads': put_spreads,
            'call_spreads': call_spreads,
            'summary': self._generate_summary(put_spreads, call_spreads)
        }
        
    def _calculate_spreads(self, options, option_type):
        """Calculate spread metrics for puts or calls"""
        spreads = []
        options = sorted(options, key=lambda x: x['strike'])
        
        for i in range(len(options) - 1):
            short_opt = options[i]
            long_opt = options[i + 1]
            
            if option_type == 'put':
                spread_width = long_opt['strike'] - short_opt['strike']
            else:
                spread_width = short_opt['strike'] - long_opt['strike']
                
            credit = short_opt['bid'] - long_opt['ask']
            
            if credit <= 0 or not all(k in short_opt for k in ['bid', 'ask', 'delta']):
                continue
                
            spreads.append({
                'short_strike': short_opt['strike'],
                'long_strike': long_opt['strike'],
                'width': spread_width,
                'credit': credit,
                'probability': 1 - short_opt['delta'] if option_type == 'put' else short_opt['delta'],
                'risk_reward': (spread_width - credit) / credit if credit > 0 else 0,
                'type': option_type,
                'short_iv': short_opt['iv'],
                'long_iv': long_opt['iv']
            })
            
        return sorted(spreads, key=lambda x: x['risk_reward'], reverse=True)
        
    def _generate_summary(self, put_spreads, call_spreads):
        """Generate summary statistics"""
        best_put = max(put_spreads, key=lambda x: x['risk_reward']) if put_spreads else None
        best_call = max(call_spreads, key=lambda x: x['risk_reward']) if call_spreads else None
        
        return {
            'best_put': best_put,
            'best_call': best_call,
            'avg_put_credit': np.mean([s['credit'] for s in put_spreads]) if put_spreads else 0,
            'avg_call_credit': np.mean([s['credit'] for s in call_spreads]) if call_spreads else 0,
            'total_spreads': len(put_spreads) + len(call_spreads)
        }
        
    def _empty_summary(self):
        return {
            'best_put': None,
            'best_call': None,
            'avg_put_credit': 0,
            'avg_call_credit': 0,
            'total_spreads': 0
        }