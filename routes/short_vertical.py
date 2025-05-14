from flask import Blueprint, render_template, jsonify, current_app, request

bp = Blueprint('shortvertical', __name__)

@bp.route('/')
def shortvertical_dashboard():
    return render_template('analyzers/short_vertical.html')

@bp.route('/analyze', methods=['POST'])
def run_combined_analysis():
    print("=====================================Running combined analysis for short verticals")
    call_analyzer = current_app.analyzers.get('shortvertical_call')
    put_analyzer = current_app.analyzers.get('shortvertical_put')

    if not call_analyzer or not put_analyzer:
        return jsonify({'error': 'One or both analyzers not found'}), 500

    call_result = call_analyzer.analyze_market()
    put_result = put_analyzer.analyze_market()

    return jsonify({
        'status': 'completed',
        'timestamp': max(call_result['timestamp'], put_result['timestamp'])
    })

@bp.route('/data')
def get_combined_data():
    print("=====================================Getting combined data for short verticals")
    call_analyzer = current_app.analyzers.get('shortvertical_call')
    put_analyzer = current_app.analyzers.get('shortvertical_put')

    if not call_analyzer or not put_analyzer:
        return jsonify({'error': 'One or both analyzers not found'}), 500

    return jsonify({
        'call': call_analyzer.current_analysis,
        'put': put_analyzer.current_analysis
    })


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
