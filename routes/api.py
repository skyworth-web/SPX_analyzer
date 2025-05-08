from flask import Blueprint, request, jsonify
from models import SPXAnalysis, SPXOptionStream, SPXSpot, Position
from datetime import datetime, timedelta
from analyzers.base import BaseAnalyzer

bp = Blueprint('api', __name__)

@bp.route('/analyzer/<name>/results')
def analyzer_results(name):
    """Get latest results for specific analyzer"""
    hours = request.args.get('hours', default=24, type=int)
    limit = request.args.get('limit', default=100, type=int)
    
    cutoff = datetime.now() - timedelta(hours=hours)
    
    results = SPXAnalysis.query.filter(
        SPXAnalysis.analyzer_name == name,
        SPXAnalysis.timestamp >= cutoff
    ).order_by(SPXAnalysis.timestamp.desc()).limit(limit).all()
    
    return jsonify([r.data for r in results])

@bp.route('/options/stream')
def options_stream():
    """Get recent options chain data"""
    minutes = request.args.get('minutes', default=5, type=int)
    strike_min = request.args.get('strike_min', type=float)
    strike_max = request.args.get('strike_max', type=float)
    option_type = request.args.get('type')
    
    cutoff = datetime.now() - timedelta(minutes=minutes)
    query = SPXOptionStream.query.filter(
        SPXOptionStream.timestamp >= cutoff
    )
    
    if strike_min:
        query = query.filter(SPXOptionStream.strike >= strike_min)
    if strike_max:
        query = query.filter(SPXOptionStream.strike <= strike_max)
    if option_type:
        query = query.filter(SPXOptionStream.option_type == option_type)
    
    options = query.order_by(
        SPXOptionStream.option_type,
        SPXOptionStream.strike
    ).all()
    
    return jsonify([{
        'strike': o.strike,
        'type': o.option_type,
        'expiry': o.expiry_date.isoformat(),
        'iv': o.iv,
        'delta': o.delta,
        'gamma': o.gamma,
        'bid': o.bid,
        'ask': o.ask,
        'volume': o.volume,
        'oi': o.open_interest,
        'timestamp': o.timestamp.isoformat()
    } for o in options])

@bp.route('/spot')
def spot_price():
    """Get current spot price"""
    spot = SPXSpot.query.order_by(SPXSpot.timestamp.desc()).first()
    return jsonify({
        'price': spot.price if spot else None,
        'timestamp': spot.timestamp.isoformat() if spot else None
    })

@bp.route('/positions')
def get_positions():
    """Get current positions"""
    status = request.args.get('status', default='open')
    limit = request.args.get('limit', default=100, type=int)
    
    positions = Position.query.filter(
        Position.status == status
    ).order_by(Position.entry_time.desc()).limit(limit).all()
    
    return jsonify([{
        'id': p.id,
        'symbol': p.symbol,
        'type': p.position_type,
        'entry_time': p.entry_time.isoformat(),
        'entry_price': p.entry_price,
        'exit_time': p.exit_time.isoformat() if p.exit_time else None,
        'exit_price': p.exit_price,
        'quantity': p.quantity,
        'status': p.status,
        'analyzer': p.analyzer_source,
        'legs': p.legs
    } for p in positions])