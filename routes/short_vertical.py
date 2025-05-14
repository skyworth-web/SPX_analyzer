from flask import Blueprint, render_template, jsonify, current_app, request

bp = Blueprint('shortvertical', __name__)

@bp.route('/<option_type>')
def shortvertical_dashboard(option_type):
    if option_type not in ['call', 'put']:
        return "Invalid option type", 404
    return render_template('analyzers/shortvertical.html', option_type=option_type)

@bp.route('/<option_type>/status')
def shortvertical_status(option_type):
    analyzer = current_app.analyzers.get(f'shortvertical_{option_type}')
    if not analyzer:
        return jsonify({'error': 'Analyzer not found'}), 500
    return jsonify(analyzer.get_analyzer_status())

@bp.route('/<option_type>/analyze', methods=['POST'])
def run_shortvertical_analysis(option_type):
    analyzer = current_app.analyzers.get(f'shortvertical_{option_type}')
    if not analyzer:
        return jsonify({'error': 'Analyzer not found'}), 500
    result = analyzer.analyze_market()
    return jsonify({'status': 'completed', 'timestamp': result['timestamp']})

@bp.route('/<option_type>/data')
def shortvertical_data(option_type):
    analyzer = current_app.analyzers.get(f'shortvertical_{option_type}')
    if not analyzer:
        return jsonify({'error': 'Analyzer not found'}), 500
    return jsonify(analyzer.current_analysis)
