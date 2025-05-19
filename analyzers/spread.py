import pandas as pd
import numpy as np
from psycopg2 import sql
from psycopg2.extras import execute_batch
import threading
from datetime import datetime, time
import logging
from typing import List, Dict, Tuple, Any
from analyzers.base import BaseAnalyzer
from models import db, SPXOptionStream, CreditSpreadMetrics
import pytz
from flask import current_app
from sqlalchemy import func
import time as int_time
from decimal import Decimal, InvalidOperation

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
        self.running = False
        self.cst_tz = pytz.timezone('America/New_York')
        
    def fetch_options_data(self):
        with current_app.app_context():
            try:
                options = db.session.execute(
                    db.select(SPXOptionStream)
                    .order_by(SPXOptionStream.timestamp.desc())
                ).scalars()
            except Exception as e:
                logger.error(f"Error fetching options data: {e}")
                return []

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
            return df


    def find_nearest_delta_options(self, options_df, target_delta, option_type):
        """
        Find options with deltas closest to the target delta
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
            
        # Calculate mid prices
        short_leg_mid = (option['bid'] + option['ask']) / 2
        long_leg_mid = (target_option['bid'] + target_option['ask']) / 2

        # Theoretical credit of the spread
        credit = short_leg_mid - long_leg_mid
        # Only include valid spreads (positive credit)
        if credit <= 0:
            return None
        
        return {
            'credit': credit
        }

    def store_data(self, spread_data):
        with current_app.app_context():
            # Create the table if it doesn't exist
            try:
                CreditSpreadMetrics.__table__.create(db.engine, checkfirst=True)
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                
            cst_time = datetime.now(self.cst_tz)
            print("====================cst_time:", cst_time)
            rows = [
                CreditSpreadMetrics(
                    timestamp=cst_time,
                    option_type=entry['option_type'],
                    delta_bucket=float(entry['delta_bucket']),
                    point_spread=int(entry['point_spread']),
                    credit=float(entry['credit'])
                )
                for entry in spread_data
            ]
            db.session.bulk_save_objects(rows)
            db.session.commit()

    def analyze(self):
        print("=============================Analyzing...")
        try:
            with current_app.app_context():
                options_data = self.fetch_options_data()
                combined_data = []

                for option_type in ['call', 'put']:
                    self.options_type = option_type
                    spread_data = self.calculate_credit_spreads(options_data)
                    combined_data.extend(spread_data)

                self.store_data(combined_data)
                self.current_analysis = {
                    'timestamp': datetime.now(self.cst_tz),
                    'results': combined_data
                }
                return self.current_analysis

        except Exception as e:
            logger.error(f"Error processing spread analysis: {e}")
            return {'timestamp': None, 'results': []}

    def start_periodic_analysis(self):
        """Start the periodic analysis in a separate thread."""
        if self.running:
            logger.warning("Periodic analysis is already running.")
            return
        
        # Get the application context before starting the thread
        app = current_app._get_current_object()
        
        def run_periodic_analysis():
            """Wrapper function to maintain application context"""
            with app.app_context():
                self.periodic_analysis()
        
        self.running = True
        self.analysis_thread = threading.Thread(
            target=run_periodic_analysis,
            daemon=True
        )
        self.analysis_thread.start()

    def periodic_analysis(self):
        """Run the analysis periodically"""
        while self.running:
            try:
                start_time = int_time.time()
                
                # Perform analysis
                analysis_result = self.analyze()
                if not analysis_result or not analysis_result.get('results'):
                    logger.warning("Analysis returned empty results")
                
                # Calculate time taken and adjust sleep time
                processing_time = int_time.time() - start_time
                sleep_time = max(0, self.UPDATE_INTERVAL - processing_time)
                int_time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in periodic analysis: {str(e)}")
                int_time.sleep(self.UPDATE_INTERVAL)  # Wait before retrying

    def stop_analysis(self):
        """Stop the periodic analysis"""
        if not self.running:
            return
        
        self.running = False
        if hasattr(self, 'analysis_thread'):
            self.analysis_thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            if self.analysis_thread.is_alive():
                logger.warning("Analysis thread did not stop gracefully")


    def get_latest_results(self):
        """
        Fetch credit spread metrics grouped by option_type (Call/Put) as top-level,
        then by point spreads and time buckets with min/max/avg calculations.
        """
        print("=============================get_latest_results...")
        try:
            # Define time buckets
            time_buckets = [
                ("8:30-8:45", 8, 30, 8, 45),
                ("8:45-9:00", 8, 45, 9, 0),
                ("9:00-9:15", 9, 0, 9, 15),
                ("9:15-9:30", 9, 15, 9, 30),
                ("9:30-10:00", 9, 30, 10, 0),
                ("10:00-10:30", 10, 0, 10, 30),
                ("10:30-11:00", 10, 30, 11, 0),
                ("11:00-11:30", 11, 0, 11, 30),
                ("11:30-12:00", 11, 30, 12, 0),
                ("12:30-1:00", 12, 30, 13, 0),
                ("1:00-1:30", 13, 0, 13, 30),
                ("1:30-2:00", 13, 30, 14, 0),
                ("2:00-2:15", 14, 0, 14, 15),
                ("2:15-2:30", 14, 15, 14, 30),
                ("2:30-2:45", 14, 30, 14, 45),
                ("2:45-3:00", 14, 45, 15, 0)
            ]

            today = datetime.now(self.cst_tz).date()
            output = {'Call': {}, 'Put': {}}

            for bucket_name, start_h, start_m, end_h, end_m in time_buckets:
                try:
                    # Create time range for this bucket
                    bucket_start = self.cst_tz.localize(
                        datetime.combine(today, time(start_h, start_m)))
                    bucket_end = self.cst_tz.localize(
                        datetime.combine(today, time(end_h, end_m)))
                    
                    # Fetch all raw data for this time range
                    records = db.session.query(
                        CreditSpreadMetrics.point_spread,
                        CreditSpreadMetrics.delta_bucket,
                        CreditSpreadMetrics.option_type,
                        CreditSpreadMetrics.credit
                    ).filter(
                        CreditSpreadMetrics.timestamp >= bucket_start,
                        CreditSpreadMetrics.timestamp < bucket_end
                    ).all()
                    
                    # Process records
                    for point_spread, delta_bucket, option_type, credit in records:
                        try:
                            # Skip None values
                            if credit is None:
                                continue
                                
                            # Ensure credit is Decimal (handle both Decimal and float)
                            credit = Decimal(str(credit))
                            # print("=========credit:", credit)
                            point_key = f"{point_spread} Point"
                            delta_key = f"{float(delta_bucket):.2f}"  # Ensure float conversion
                            option_key = 'Call' if option_type == 'call' else 'Put'
                            
                            # Initialize data structures if needed
                            if point_key not in output[option_key]:
                                output[option_key][point_key] = {}
                            if bucket_name not in output[option_key][point_key]:
                                output[option_key][point_key][bucket_name] = {
                                    'Ave': {}, 'High': {}, 'Low': {}
                                }
                            
                            # Initialize delta bucket if needed
                            if delta_key not in output[option_key][point_key][bucket_name]['Ave']:
                                output[option_key][point_key][bucket_name]['Ave'][delta_key] = []
                            
                            # Append credit value
                            output[option_key][point_key][bucket_name]['Ave'][delta_key].append(credit)
                        except Exception as e:
                            logger.error(f"Error processing record: {str(e)}")
                            continue

                    
                    # Calculate final stats for this bucket
                    for option_key in ['Call', 'Put']:
                        for point_key in output[option_key]:
                            if bucket_name in output[option_key][point_key]:
                                for delta_key in output[option_key][point_key][bucket_name]['Ave']:
                                    credits = output[option_key][point_key][bucket_name]['Ave'][delta_key]
                                    if credits:  # Only calculate if we have values
                                        try:
                                            # Convert to float for rounding (handles Decimal properly)
                                            credits_float = [float(c) for c in credits]
                                            output[option_key][point_key][bucket_name]['Ave'][delta_key] = round(sum(credits_float)/len(credits_float), 2)
                                            output[option_key][point_key][bucket_name]['High'][delta_key] = round(max(credits_float), 2)
                                            output[option_key][point_key][bucket_name]['Low'][delta_key] = round(min(credits_float), 2)
                                        except Exception as e:
                                            logger.error(f"Error calculating stats for {option_key}/{point_key}/{bucket_name}/{delta_key}: {str(e)}")
                                            # Set defaults or skip
                                            continue

                except Exception as e:
                    logger.error(f"Error processing {bucket_name}: {str(e)}")
                    continue
                
            return output

        except Exception as e:
            logger.error(f"Error in get_latest_results: {str(e)}")
            return {'Call': {}, 'Put': {}}