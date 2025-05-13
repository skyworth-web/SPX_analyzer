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
logger = logging.getLogger("SPX_0DTE_ShortVertical_Analyzer")

class ShortverticalAnalyzer(BaseAnalyzer):
    # Strategy Parameters
    STRATEGY_PARAMS = {
        'aggressive': {
            'delta_range': {
                'min': 0.38,
                'max': 0.52
            },
            'wing_width': 10,
            'min_premium': 0.60
        },
        'moderate': {
            'delta_range': {
                'min': 0.18,
                'max': 0.28
            },
            'wing_width': 15,
            'min_premium': 0.40
        },
        'conservative': {
            'delta_range': {
                'min': 0.07,
                'max': 0.13
            },
            'wing_width': 25,
            'min_premium': 0.25
        }
    }

    def __init__(self):
        super().__init__()  # Call the constructor of BaseAnalyzer
        self.current_analysis = {
            'timestamp': None,
            'spx_price': None,
            'options_chain': None,
            'trade_opportunities': {
                'aggressive': None,
                'moderate': None,
                'conservative': None
            },
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


    def find_short_call_vertical_opportunities(self, data, strategy_type):
        """
        Find short call vertical spread opportunities based on strategy type.
        Returns the best opportunity (highest premium) within the specified parameters.
        """
        if not data or 'spx_price' not in data:
            logger.error("Invalid data received")
            return None

        spx_price = data['spx_price']
        calls = sorted(data.get('calls', []), key=lambda x: x['strike'])
        
        params = self.STRATEGY_PARAMS[strategy_type]
        opportunities = []
        
        # Filter call options by delta range for short leg
        short_call_candidates = [
            c for c in calls 
            if c.get('delta') and params['delta_range']['min'] <= abs(c['delta']) <= params['delta_range']['max']
        ]
        
        for short_call in short_call_candidates:
            # Calculate long call strike
            long_call_strike = short_call['strike'] + params['wing_width']
            
            # Find matching long call
            long_call = next((c for c in calls if c['strike'] == long_call_strike), None)
            
            if not long_call:
                continue

            # Calculate trade metrics
            premium = short_call['bid'] - long_call['ask']
            max_loss = params['wing_width'] - premium
            
            if premium >= params['min_premium']:
                # Create trade structure
                trade = {
                    'strategy_type': strategy_type,
                    'spx_price': spx_price,
                    'short_call': short_call['strike'],
                    'long_call': long_call['strike'],
                    'premium': round(premium, 2),
                    'max_loss': round(max_loss, 2),
                    'reward_to_risk': round(premium / max_loss, 2),
                    'short_call_delta': short_call.get('delta', 0),
                    'long_call_delta': long_call.get('delta', 0),
                    'call_volume': short_call.get('volume', 0),
                    'call_iv': short_call.get('volatility', 0),
                    'gamma': short_call.get('gamma', 0),
                    'theta': short_call.get('theta', 0),
                    'timestamp': datetime.now().isoformat()
                }
                opportunities.append(trade)
        
        # Sort by premium and return the best one
        if opportunities:
            return sorted(opportunities, key=lambda x: -x['premium'])[0]
        return None

    def process_data_callback(self, data):
        """
        Callback function to process new data from the streamer.
        Updates the global analysis state.
        """
        logger.info("Received data from streamer")
        if not data:
            logger.warning("No data received in callback")
            return
            
        # Debug: Check data structure
        logger.info(f"Data keys: {data.keys()}")
        logger.info(f"SPX price: {data.get('spx_price')}")
        calls_count = len(data.get('calls', []))
        puts_count = len(data.get('puts', []))
        logger.info(f"Calls count: {calls_count}, Puts count: {puts_count}")
        
        if calls_count > 0:
            sample_call = data['calls'][0]
            logger.info(f"Sample call: {sample_call}")
        
        try:
            # Update current analysis
            # Time now in Chicago    
            chicago_tz = pytz.timezone('America/Chicago')
            chicago_now = datetime.now(chicago_tz)
            
            self.current_analysis['timestamp'] = chicago_now.isoformat()
            self.current_analysis['spx_price'] = data['spx_price']
            self.current_analysis['options_chain'] = data
            
            # Find opportunities for each strategy type
            for strategy_type in ['aggressive', 'moderate', 'conservative']:
                opportunity = self.find_short_call_vertical_opportunities(data, strategy_type)
                self.current_analysis['trade_opportunities'][strategy_type] = opportunity
                
                if opportunity:
                    logger.info(f"{strategy_type.capitalize()} opportunity found: {opportunity}")
                else:
                    logger.info(f"No {strategy_type} opportunities found")
            
            # Save analysis to database
            # save_analysis(self.current_analysis)
            
            # Update status
            # status_data = self.get_analyzer_status()
            # update_status(status_data)
                
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            
    def get_analyzer_status(self):
        """Return the current status of the analyzer."""
        return {
            'status': 'running',
            'last_analysis': self.current_analysis['timestamp'],
            'spx_price': self.current_analysis['spx_price'],
            'aggressive_found': 1 if self.current_analysis['trade_opportunities']['aggressive'] else 0,
            'moderate_found': 1 if self.current_analysis['trade_opportunities']['moderate'] else 0,
            'conservative_found': 1 if self.current_analysis['trade_opportunities']['conservative'] else 0,
            'positions_count': len(self.current_analysis['current_positions'])
        }
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
