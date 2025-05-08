from flask import Blueprint, render_template, current_app
from datetime import datetime, timedelta
from models import SPXOptionStream

bp = Blueprint('bs_deviation', __name__)

@bp.route('/')
def bs_deviation_dashboard():
    analyzer = current_app.analyzers.get('bs_deviation')
    if not analyzer:
        return "BS Deviation Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/bs_deviation.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)