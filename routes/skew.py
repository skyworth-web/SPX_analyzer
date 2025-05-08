from flask import Blueprint, render_template, current_app

bp = Blueprint('skew', __name__)

@bp.route('/')
def skew_dashboard():
    analyzer = current_app.analyzers.get('skew')
    if not analyzer:
        return "Skew Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/skew_curve.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)