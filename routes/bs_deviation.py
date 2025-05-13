from flask import Blueprint, render_template, request, jsonify
from analyzers.bs_deviation import BSDeviationAnalyzer
import pandas as pd

bs_deviation_bp = Blueprint('bs_deviation', __name__)

@bs_deviation_bp.route('/bs-deviation')
def bs_deviation_page():
    return render_template('bs_deviation.html')

@bs_deviation_bp.route('/api/bs-deviation', methods=['POST'])
def bs_deviation_api():
    try:
        data = request.json.get('options_data')
        df = pd.DataFrame(data)
        analyzer = BSDeviationAnalyzer()
        result = analyzer.analyze(df)
        return jsonify({'status': 'success', 'results': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
