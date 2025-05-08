from flask import Blueprint, render_template, current_app
from models import db, SPXOptionStream
from datetime import datetime, timedelta

bp = Blueprint('spread', __name__)

@bp.route('/')
def spread_dashboard():
    try:
        analyzer = current_app.analyzers.get('spread')
        if not analyzer:
            return "Spread Analyzer not initialized", 500
            
        # Get market data directly for this example
        cutoff = datetime.now() - timedelta(minutes=5)
        options = SPXOptionStream.query.filter(
            SPXOptionStream.timestamp >= cutoff
        ).all()
        
        if not options:
            return render_template('analyzers/spread.html',
                                analyzer=analyzer,
                                results={
                                    'error': 'No options data available',
                                    'timestamp': datetime.now().isoformat()
                                },
                                current_app=current_app)
        
        # Simple example processing
        puts = [{
            'strike': o.strike_price,
            'bid': o.put_bid,
            'ask': o.put_ask,
            'iv': o.put_iv
        } for o in options if o.put_bid]
        
        calls = [{
            'strike': o.strike_price,
            'bid': o.call_bid,
            'ask': o.call_ask,
            'iv': o.call_iv
        } for o in options if o.call_bid]
        
        return render_template('analyzers/spread.html',
                            analyzer=analyzer,
                            results={
                                'timestamp': datetime.now().isoformat(),
                                'puts': puts,
                                'calls': calls,
                                'summary': {
                                    'put_count': len(puts),
                                    'call_count': len(calls)
                                }
                            },
                            current_app=current_app)
            
    except Exception as e:
        current_app.logger.error(f"Spread dashboard error: {str(e)}")
        return render_template('analyzers/spread.html',
                            error=str(e),
                            current_app=current_app)