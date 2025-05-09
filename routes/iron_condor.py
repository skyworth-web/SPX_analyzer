from flask import Blueprint, render_template, current_app
from datetime import datetime, timedelta
from models import SPXOptionStream

bp = Blueprint('iron_condor', __name__)

@bp.route('/')
def iron_condor_dashboard():
    analyzer = current_app.analyzers.get('iron_condor')
    if not analyzer:
        return "BS Deviation Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/iron_condor.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)