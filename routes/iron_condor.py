from flask import Blueprint, render_template, current_app, jsonify, request
from datetime import datetime, timedelta
from models import SPXOptionStream

bp = Blueprint('iron_condor', __name__)

@bp.route('/')
def iron_condor_dashboard():
    analyzer = current_app.analyzers.get('iron_condor')
    if not analyzer:
        return "Iron Condor Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/iron_condor.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)
    
@bp.route('/status')
def get_status():
    analyzer = current_app.analyzers.get('iron_condor')
    return jsonify({
        'spx_price': analyzer.current_analysis.get('spx_price'),
        'last_analysis': analyzer.current_analysis.get('timestamp')
    })

@bp.route('/analysis')
def get_analysis():
    analyzer = current_app.analyzers.get('iron_condor')
    return jsonify({
        'scored_trades': analyzer.current_analysis.get('scored_trades', []),
        'current_positions': analyzer.current_analysis.get('current_positions', [])
    })

@bp.route('/analyze', methods=['POST'])
def analyze_now():
    analyzer = current_app.analyzers.get('iron_condor')
    result = analyzer.analyze_market()
    return jsonify({'status': 'completed', 'timestamp': result['timestamp']})

@bp.route('/position', methods=['POST'])
def add_position():
    analyzer = current_app.analyzers.get('iron_condor')
    data = request.get_json()
    return jsonify(analyzer.add_position(data))

@bp.route('/position/<position_id>/close', methods=['POST'])
def close_position(position_id):
    analyzer = current_app.analyzers.get('iron_condor')
    return jsonify(analyzer.close_position(position_id))