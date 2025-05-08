from flask import Blueprint, render_template
from flask import current_app

bp = Blueprint('spread', __name__)

@bp.route('/')
def spread_dashboard():
    analyzer = current_app.analyzers['spread']
    results = analyzer.get_latest_results()
    return render_template('analyzers/spread.html', 
                         analyzer=analyzer,
                         results=results)

@bp.route('/data')
def spread_data():
    analyzer = current_app.analyzers['spread']
    return analyzer.get_latest_results()