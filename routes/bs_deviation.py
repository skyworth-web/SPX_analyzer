from flask import Blueprint, render_template, jsonify
from analyzers.bs_deviation import BSDeviationAnalyzer

bp = Blueprint('bs_deviation', __name__)

@bp.route('/')
def bs_deviation_dashboard():
    return render_template('analyzers/bs_deviation.html')

@bp.route('/data')
def bs_deviation_data():
    analyzer = BSDeviationAnalyzer()
    data = analyzer.analyze()

    calls = [row for row in data if row['option_type'] == 'call']
    puts = [row for row in data if row['option_type'] == 'put']

    return jsonify({'calls': calls, 'puts': puts})
