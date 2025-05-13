import json
import logging
import uuid
from datetime import datetime
import pytz
from analyzers.base import BaseAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SPX_0DTE_IronCondor_Analyzer")

class IroncondorAnalyzer(BaseAnalyzer):
    # Strategy Parameters
    STRATEGY_PARAMS = {
        'delta_range': {
            'min': 0.12,
            'max': 0.22
        },
        'wing_width': 20,
        'min_premium': 0.50,
        'max_risk': 15.00,
        'scoring_weights': {
            'premium': 0.25,
            'risk_reward': 0.25,
            'delta_balance': 0.15,
            'volume_liquidity': 0.15,
            'volatility': 0.10,
            'greeks': 0.10
        }
    }

    def __init__(self):
        super().__init__()  # Call the constructor of BaseAnalyzer
        self.current_analysis = {
            'timestamp': None,
            'spx_price': None,
            'options_chain': None,
            'scored_trades': None,
            'current_positions': [],
            'recommendations': {
                'entries': [],
                'exits': [],
                'adjustments': []
            }
        }
        initial_data = self.get_latest_results()  # Use the inherited method
        if initial_data:
            self.process_data_callback(initial_data)
            logger.info("Initial data processed successfully")
        else:
            logger.warning("No initial data available")
    def calculate_trade_score(self, trade):
        """
        Calculate a comprehensive score for a potential iron condor trade.
        Returns a score between 0 and 100.
        """
        score = 0
        
        try:
            # 1. Premium Score (25%)
            premium_score = min(trade['premium'] / self.STRATEGY_PARAMS['min_premium'], 2.0) * 50
            score += premium_score * self.STRATEGY_PARAMS['scoring_weights']['premium']
            
            # 2. Risk/Reward Score (25%)
            rr_ratio = trade['premium'] / trade['max_loss']
            rr_score = min(rr_ratio / 0.3, 1.0) * 100  # Target 0.3 RR ratio
            score += rr_score * self.STRATEGY_PARAMS['scoring_weights']['risk_reward']
            
            # 3. Delta Balance Score (15%)
            delta_diff = abs(abs(trade['short_call_delta']) - abs(trade['short_put_delta']))
            delta_score = (1 - min(delta_diff / 0.05, 1.0)) * 100  # Target < 0.05 delta difference
            score += delta_score * self.STRATEGY_PARAMS['scoring_weights']['delta_balance']
            
            # 4. Volume/Liquidity Score (15%)
            volume_score = min(
                (trade['call_volume'] + trade['put_volume']) / 100,
                1.0
            ) * 100
            score += volume_score * self.STRATEGY_PARAMS['scoring_weights']['volume_liquidity']
            
            # 5. Volatility Score (10%)
            avg_iv = (trade['call_iv'] + trade['put_iv']) / 2
            iv_score = min(avg_iv / 30, 2.0) * 50  # Score increases with IV up to 60%
            score += iv_score * self.STRATEGY_PARAMS['scoring_weights']['volatility']
            
            # 6. Greeks Score (10%)
            gamma_score = min(trade['gamma'] / 0.005, 1.0) * 100
            theta_score = min(abs(trade['theta']) / 5, 1.0) * 100
            greeks_score = (gamma_score + theta_score) / 2
            score += greeks_score * self.STRATEGY_PARAMS['scoring_weights']['greeks']
            
            return max(0, min(100, round(score, 2)))  # Ensure score is between 0 and 100
            
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return 0

    def find_iron_condor_opportunities(self, data):
        """
        Main function to find and score iron condor opportunities.
        Returns a list of scored opportunities sorted by score.
        """
        if not data or 'spx_price' not in data:
            logger.error("Invalid data received")
            return []

        spx_price = data['spx_price']
        calls = sorted(data.get('calls', []), key=lambda x: x['strike'])
        puts = sorted(data.get('puts', []), key=lambda x: x['strike'], reverse=True)
        
        opportunities = []
        
        # Filter options by delta range
        short_call_candidates = [
            c for c in calls 
            if c.get('delta') and self.STRATEGY_PARAMS['delta_range']['min'] <= abs(c['delta']) <= self.STRATEGY_PARAMS['delta_range']['max']
        ]
        short_put_candidates = [
            p for p in puts 
            if p.get('delta') and self.STRATEGY_PARAMS['delta_range']['min'] <= abs(p['delta']) <= self.STRATEGY_PARAMS['delta_range']['max']
        ]
        
        for short_put in short_put_candidates:
            for short_call in short_call_candidates:
                # Calculate wing strikes
                long_put_strike = short_put['strike'] - self.STRATEGY_PARAMS['wing_width']
                long_call_strike = short_call['strike'] + self.STRATEGY_PARAMS['wing_width']
                
                # Find long options
                long_put = next((p for p in puts if p['strike'] == long_put_strike), None)
                long_call = next((c for c in calls if c['strike'] == long_call_strike), None)
                
                if not long_put or not long_call:
                    continue

                # Calculate trade metrics
                premium = (
                    short_put['bid'] - long_put['ask'] +
                    short_call['bid'] - long_call['ask']
                )
                max_loss = self.STRATEGY_PARAMS['wing_width'] - premium
                print('==================== before')
                if premium >= self.STRATEGY_PARAMS['min_premium'] and max_loss <= self.STRATEGY_PARAMS['max_risk']:
                    # Create trade structure
                    print('==================== here')
                    trade = {
                        'spx_price': spx_price,
                        'short_put': short_put['strike'],
                        'long_put': long_put['strike'],
                        'short_call': short_call['strike'],
                        'long_call': long_call['strike'],
                        'premium': round(premium, 2),
                        'max_loss': round(max_loss, 2),
                        'reward_to_risk': round(premium / max_loss, 2),
                        'short_call_delta': short_call.get('delta', 0),
                        'long_call_delta': long_call.get('delta', 0),
                        'short_put_delta': short_put.get('delta', 0),
                        'long_put_delta': long_put.get('delta', 0),
                        'call_volume': short_call.get('volume', 0),
                        'put_volume': short_put.get('volume', 0),
                        'call_iv': short_call.get('volatility', 0),
                        'put_iv': short_put.get('volatility', 0),
                        'gamma': (short_call.get('gamma', 0) + short_put.get('gamma', 0)) / 2,
                        'theta': (short_call.get('theta', 0) + short_put.get('theta', 0)) / 2,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Calculate and add score
                    trade['score'] = self.calculate_trade_score(trade)
                    opportunities.append(trade)
        
        # Sort by score and return top opportunities
        return sorted(opportunities, key=lambda x: -x['score'])[:5]

    def process_data_callback(self, data):
        """
        Callback function to process new data from the streamer.
        Updates the global analysis state.
        """
        logger.info("Received data from streamer")
        if not data:
            logger.warning("No data received in callback")
            return
            
        try:
            # Update current analysis
            ## Time now in Chicago    
            chicago_tz = pytz.timezone('America/Chicago')
            chicago_now = datetime.now(chicago_tz)
            
            self.current_analysis['timestamp'] = chicago_now.isoformat()
            self.current_analysis['spx_price'] = data['spx_price']
            self.current_analysis['options_chain'] = data
            
            # Find and score opportunities
            opportunities = self.find_iron_condor_opportunities(data)
            self.current_analysis['scored_trades'] = opportunities
            
            # Log results
            if opportunities:
                logger.info(f"Found {len(opportunities)} opportunities")
                for op in opportunities:
                    logger.info(f"Trade Opportunity (Score: {op['score']}): {op}")
            else:
                logger.info("No trade opportunities found")
                
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def analyze_market(self):
        """
        Manually trigger market analysis.
        Returns the current analysis after processing.
        """
        logger.info("Manually triggering market analysis...")
        data = self.get_latest_results()  # Use the inherited method
        self.process_data_callback(data)
        return self.current_analysis

    def add_position(self, position_data):
        """
        Add a new position to the current analysis.
        Args:
            position_data: Dictionary containing position details
        Returns:
            Dictionary with status and position ID
        """
        try:
            # Generate a unique ID for the position
            position_id = str(uuid.uuid4())
            
            # Add timestamp and ID to position data
            position_data['id'] = position_id
            position_data['timestamp'] = datetime.now().isoformat()
            position_data['closed'] = False

            # Add to current positions
            self.current_analysis['current_positions'].append(position_data)
            
            logger.info(f"Added new position: {position_id}")
            return {
                'status': 'success',
                'position_id': position_id,
                'position': position_data
            }
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def close_position(self, position_id):
        """
        Close an existing position.
        Args:
            position_id: ID of the position to close
        Returns:
            Dictionary with status and closed position details
        """
        try:
            # Find the position
            position = next(
                (p for p in self.current_analysis['current_positions'] if p['id'] == position_id),
                None
            )
            
            if not position:
                raise ValueError(f"Position {position_id} not found")
                
            # Mark as closed and add close timestamp
            position['closed'] = True
            position['close_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"Closed position: {position_id}")
            return {
                'status': 'success',
                'position_id': position_id,
                'position': position
            }
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

