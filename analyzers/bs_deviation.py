from dashboards.analyzers.base import BaseAnalyzer
from datetime import datetime
import numpy as np

class BSDeviationAnalyzer(BaseAnalyzer):
    name = "bs_deviation"
    description = "Black-Scholes Deviation Analyzer"
    refresh_interval = 60  # seconds

    def analyze(self, market_data):
        if not market_data or not market_data.get('expirations'):
            return {
                'timestamp': datetime.now().isoformat(),
                'error': 'No market data available',
                'deviations': []
            }

        deviations = []
        for expiry, data in market_data['expirations'].items():
            for option in data['puts'] + data['calls']:
                if all(k in option for k in ['bid', 'ask', 'iv']):
                    # Simplified BS deviation calculation (replace with your actual model)
                    theo_price = (option['bid'] + option['ask']) / 2 * 0.95  # Example calculation
                    deviation = (option['midpoint'] - theo_price) / theo_price if theo_price else 0
                    
                    deviations.append({
                        'strike': option['strike'],
                        'type': 'put' if 'put' in option else 'call',
                        'market': option['midpoint'],
                        'theoretical': theo_price,
                        'deviation': deviation,
                        'iv': option['iv']
                    })

        return {
            'timestamp': datetime.now().isoformat(),
            'deviations': sorted(deviations, key=lambda x: abs(x['deviation']), reverse=True)[:50],  # Top 50
            'summary': {
                'max_deviation': max([abs(d['deviation']) for d in deviations]) if deviations else 0,
                'avg_deviation': np.mean([abs(d['deviation']) for d in deviations]) if deviations else 0
            }
        }