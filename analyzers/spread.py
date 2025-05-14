import pandas as pd
import numpy as np
from psycopg2 import sql
from psycopg2.extras import execute_batch
import threading
from datetime import datetime
import logging
from typing import List, Dict, Tuple, Any
from analyzers.base import BaseAnalyzer
from models import db, SPXOptionStream, CreditSpreadMetrics

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpreadAnalyzer(BaseAnalyzer):
# Configuration
    DELTA_BUCKETS = [0.10, 0.14, 0.18, 0.22, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70]
    POINT_SPREADS = [5, 10, 15, 20, 25]
    UPDATE_INTERVAL = 15  # seconds

    def __init__(self, options_type = 'call'):
        super().__init__()
        self.options_type = options_type
        self.current_analysis = {'timestamp': None, 'results': []}
        
    def fetch_options_data(self):
        options = db.session.execute(
            db.select(SPXOptionStream)
            .order_by(SPXOptionStream.timestamp.desc())
        ).scalars()

        strike, expiration, option_type, bid, ask, delta = [], [], [], [], [], []

        for opt in options:
            # Call
            strike.append(opt.strike_price)
            expiration.append(opt.exp_date)
            option_type.append('call')
            bid.append(opt.call_bid)
            ask.append(opt.call_ask)
            delta.append(opt.call_delta)

            # Put
            strike.append(opt.strike_price)
            expiration.append(opt.exp_date)
            option_type.append('put')
            bid.append(opt.put_bid)
            ask.append(opt.put_ask)
            delta.append(opt.put_delta)

        df = pd.DataFrame({
            'strike': strike,
            'expiration': expiration,
            'option_type': option_type,
            'bid': bid,
            'ask': ask,
            'delta': delta
        })
        df['mid'] = (df['bid'] + df['ask']) / 2
        logger.debug(f"Fetched {len(df)} options")
        return df


    def find_nearest_delta_options(self, options_df, target_delta, option_type):
        """
        Find options with deltas closest to the target delta
        
        Args:
            options_df: DataFrame of options data
            target_delta: The target delta value
            option_type: 'call' or 'put'
        
        Returns:
            DataFrame with options filtered by type and sorted by proximity to target delta
        """
        # Filter by option type
        filtered = options_df[options_df['option_type'] == option_type].copy()
        
        # For puts, we use absolute value for comparison since puts have negative deltas
        if option_type == 'put':
            target_delta = -abs(target_delta)
            filtered['delta_diff'] = abs(filtered['delta'] - target_delta)
        else:
            filtered['delta_diff'] = abs(filtered['delta'] - target_delta)
        
        # Sort by delta difference
        return filtered.sort_values('delta_diff')

    def calculate_credit_spreads(self, options_df, expiration_filter=None):
        """
        Calculate credit spread data for all combinations of delta buckets and point spreads
        
        Args:
            options_df: DataFrame with options data
            expiration_filter: Optional filter for specific expirations
        
        Returns:
            List of dictionaries with spread data
        """
        results = []
        
        # Filter by expiration if provided
        if expiration_filter:
            options_df = options_df[options_df['expiration'] == expiration_filter]
        
        # Process each option type
        for option_type in ['call', 'put']:
            # Process each delta bucket
            for delta in self.DELTA_BUCKETS:
                # Find options closest to this delta
                delta_options = self.find_nearest_delta_options(options_df, delta, option_type)
                
                if len(delta_options) == 0:
                    continue
                    
                # Get the best match
                best_match = delta_options.iloc[0]
                
                # For each point spread
                for spread in self.POINT_SPREADS:
                    spread_data = self.calculate_spread_for_option(
                        options_df, 
                        best_match, 
                        spread, 
                        option_type
                    )
                    
                    if spread_data:
                        spread_data.update({
                            'option_type': option_type,
                            'delta_bucket': delta,
                            'point_spread': spread
                        })
                        results.append(spread_data)
        
        return results

    def calculate_spread_for_option(self, options_df, option, point_spread, option_type):
        """
        Calculate spread data for a specific option and point spread
        
        Args:
            options_df: DataFrame with options data
            option: The base option (Series)
            point_spread: The point spread value
            option_type: 'call' or 'put'
        
        Returns:
            Dictionary with spread data or None if not enough data
        """
        base_strike = option['strike']
        expiration = option['expiration']
        
        # Filter options by expiration date
        same_exp_options = options_df[
            (options_df['expiration'] == expiration) & 
            (options_df['option_type'] == option_type)
        ]
        
        if len(same_exp_options) == 0:
            return None
        
        # Calculate target strike based on option type and point spread
        if option_type == 'call':
            # For calls, we're selling at base_strike and buying at base_strike + point_spread
            target_strike = base_strike + point_spread
            # Filter for options with target strike
            target_options = same_exp_options[same_exp_options['strike'] >= target_strike].sort_values('strike')
        else:  # put
            # For puts, we're selling at base_strike and buying at base_strike - point_spread
            target_strike = base_strike - point_spread
            # Filter for options with target strike
            target_options = same_exp_options[same_exp_options['strike'] <= target_strike].sort_values('strike', ascending=False)
        
        if len(target_options) == 0:
            return None
        
        # Get the closest match to our target strike
        target_option = target_options.iloc[0]
        
        # Calculate credit for the spread
        if option_type == 'call':
            # Sell base option, buy target option
            credit = option['bid'] - target_option['ask']
        else:  # put
            # Sell base option, buy target option
            credit = option['bid'] - target_option['ask']
        
        # Only include valid spreads (positive credit)
        if credit <= 0:
            return None
        
        # For demonstration purposes, we're using the same credit for avg/high/low
        # In a real implementation, you'd track these separately over time
        return {
            'avg_credit': credit,
            'high_credit': credit,
            'low_credit': credit
        }

    def store_data(self, spread_data):
        # Create the table if it doesn't exist
        try:
            CreditSpreadMetrics.__table__.create(db.engine, checkfirst=True)
        except Exception as e:
            logger.error(f"Error creating table: {e}")
        now = datetime.utcnow()
        rows = [
            CreditSpreadMetrics(
                timestamp=now,
                option_type=entry['option_type'],
                delta_bucket=float(entry['delta_bucket']),
                point_spread=int(entry['point_spread']),
                avg_credit=float(entry['avg_credit']),
                high_credit=float(entry['high_credit']),
                low_credit=float(entry['low_credit'])
            )
            for entry in spread_data
        ]
        db.session.bulk_save_objects(rows)
        db.session.commit()



    def analyze(self):
        try:
            options_data = self.fetch_options_data()
            combined_data = []

            for option_type in ['call', 'put']:
                self.options_type = option_type
                spread_data = self.calculate_credit_spreads(options_data)
                combined_data.extend(spread_data)

            self.store_data(combined_data)
            self.current_analysis = {
                'timestamp': datetime.utcnow(),
                'results': combined_data
            }
            return self.current_analysis

        except Exception as e:
            logger.error(f"Error processing spread analysis: {e}")
            return {'timestamp': None, 'results': []}


    def get_latest_results(self):
        return self.current_analysis.get('result', [])
