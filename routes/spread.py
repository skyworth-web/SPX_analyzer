from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime
from models import CreditSpreadMetrics
from analyzers.spread import SpreadAnalyzer

bp = Blueprint('spread', __name__)

@bp.route('/')
def spread_dashboard():
    return render_template('analyzers/spread.html')

@bp.route('/status')
def spread_status():
    analyzer = current_app.analyzers.get('spread')
    if not analyzer:
        return jsonify({'error': 'Spread Analyzer not initialized'}), 500

    return jsonify({
        'last_run': analyzer.current_analysis.get('timestamp'),
        'records': len(analyzer.current_analysis.get('results', []))
    })

@bp.route('/analyze', methods=['POST'])
def run_analysis():
    analyzer = current_app.analyzers.get('spread')
    if not analyzer:
        return jsonify({'error': 'Analyzer not found'}), 500
    analyzer.start_periodic_analysis()
    results = analyzer.get_latest_results()
    
    result = analyzer.analyze()
    return jsonify({'status': 'completed', 'timestamp': result['timestamp']})

@bp.route('/data')
async def spread_data():
    analyzer = current_app.analyzers.get('spread')
    analyzer.start_periodic_analysis()
    results = analyzer.get_latest_results()
    
    return jsonify(results)