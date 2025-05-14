from flask import Blueprint, render_template, request, jsonify
from analyzers.bs_deviation import BSDeviationAnalyzer
import pandas as pd

bp = Blueprint('bs_deviation', __name__)

@bp.route('/')
def bs_deviation_dashboard():
    return render_template('analyzers/bs_deviation.html')

@bp.route('/bs-deviation/api', methods=['POST'])
def bs_deviation_api():
    try:
        data = request.json.get('options_data')
        df = pd.DataFrame(data)
        analyzer = BSDeviationAnalyzer()
        result = analyzer.analyze(df)
        return jsonify({'status': 'success', 'results': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
