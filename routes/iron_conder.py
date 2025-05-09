from flask import Blueprint, render_template, current_app
from datetime import datetime, timedelta
from models import SPXOptionStream

bp = Blueprint('iron_conder', __name__)

@bp.route('/')
def iron_conder_dashboard():
    analyzer = current_app.analyzers.get('iron_conder')
    if not analyzer:
        return "BS Deviation Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/iron_conder.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)