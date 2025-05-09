import logging
from datetime import datetime, timedelta
from models import db, SPXOptionStream, SPXSpot

class BaseAnalyzer:
    name = "base"
    description = "Base analyzer class"
    refresh_interval = 30  # seconds
    
    def __init__(self):
        self.last_run = None
        self.last_results = None
        self.logger = logging.getLogger(f"analyzer.{self.name}")
        self.spot_price = None
        
    # def analyze(self, market_data):
    #     """To be implemented by each analyzer"""
    #     raise NotImplementedError
        
    def get_latest_results(self):
        """Get cached results or fetch new ones"""
        if not self.last_results or self._needs_refresh():
            market_data = self._fetch_market_data()
            if market_data:
                return market_data
        return self.last_results or {
            'timestamp': datetime.now().isoformat(),
            'spot_price': None,
            'error': 'No market data available'
        }
        
    def _needs_refresh(self):
        if not self.last_run:
            return True
        return (datetime.now() - self.last_run).seconds > self.refresh_interval
        
    def _fetch_market_data(self):
        """Fetch market data from database tables"""
        try:
            # Get current spot price
            spot = db.session.execute(
                db.select(SPXOptionStream)
                .order_by(SPXOptionStream.timestamp.desc())
                .limit(1)
            ).scalar()
            self.spot_price = spot.strike_price if spot else None

            # Get options data from last 5 minutes (increased from 2)
            cutoff = datetime.now() - timedelta(minutes=5)
            
            options = db.session.execute(
                db.select(SPXOptionStream)
                .where(SPXOptionStream.timestamp >= cutoff)
                .order_by(SPXOptionStream.timestamp.desc())
            ).scalars().all()

            # options = db.session.query(SPXOptionStream).limit(10).all()
            
            if not options:
                self.logger.warning(f"No options data found since {cutoff}")
                # Return minimal data structure to prevent template errors
                return {
                    'timestamp': datetime.now().isoformat(),
                    'spot_price': self.spot_price,
                    'puts': [],
                    'calls': [],
                    'error': 'No options data available'
                }
                
            # Organize data by expiration and strike
            organized_data = {}
            for opt in options:
                # if opt.exp_date not in organized_data:
                #     organized_data = {'calls': [], 'puts': []}
                
                organized_data['calls'].append({
                    'strike': opt.strike_price,
                    'bid': opt.call_bid,
                    'ask': opt.call_ask,
                    'last': opt.call_last,
                    'volatility': opt.call_iv,
                    'delta': opt.call_delta,
                    'gamma': opt.call_gamma,
                    'theta': opt.call_theta,
                    'vega': opt.call_vega,
                    'openInterest': opt.call_open_int,
                    'net_change': opt.call_net_chg,
                    'timestamp': opt.timestamp.isoformat(),
                    'daysToExpiration': 0,
                    'type': 'C'
                })
                
                organized_data['puts'].append({
                    'strike': opt.strike_price,
                    'bid': opt.put_bid,
                    'ask': opt.put_ask,
                    'last': opt.put_last,
                    'volatility': opt.put_iv,
                    'delta': opt.put_delta,
                    'gamma': opt.put_gamma,
                    'theta': opt.put_theta,
                    'vega': opt.put_vega,
                    'openInterest': opt.put_open_int,
                    'net_change': opt.put_net_chg,
                    'timestamp': opt.timestamp.isoformat(),
                    'daysToExpiration': 0,
                    'type': 'P'
                })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'spx_price': self.spot_price,
                'calls': organized_data['calls'],
                'puts': organized_data['puts']
                #'primary_expiry': min(organized_data.keys()) if organized_data else None
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch market data: {str(e)}")
            return None
        
    def _log_results(self, results):
        """Store results to spx_analysis table"""
        if not results or 'error' in results:
            return
            
        try:
            record = SPXAnalysis(
                timestamp=datetime.now(),
                spx_price=results.get('spot_price'),
                opportunity={
                    'analyzer': self.name,
                    'data': results
                }
            )
            
            db.session.add(record)
            db.session.commit()
            
            self.last_results = results
            self.last_run = datetime.now()
            self.logger.info(f"Analysis completed at {self.last_run}")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to save results: {str(e)}")