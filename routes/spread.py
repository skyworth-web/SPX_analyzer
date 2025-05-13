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

    result = analyzer.analyze()
    return jsonify({'status': 'completed', 'timestamp': result['timestamp']})

@bp.route('/data')
def spread_data():
    data = CreditSpreadMetrics.query.order_by(CreditSpreadMetrics.timestamp.desc()).limit(100).all()
    results = [
        {
            'timestamp': r.timestamp.isoformat(),
            'option_type': r.option_type,
            'delta_bucket': r.delta_bucket,
            'point_spread': r.point_spread,
            'avg_credit': r.avg_credit,
            'high_credit': r.high_credit,
            'low_credit': r.low_credit
        }
        for r in data
    ]
    return jsonify(results)
