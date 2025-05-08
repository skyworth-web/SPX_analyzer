from flask import Blueprint, render_template, current_app

bp = Blueprint('macro_overlay', __name__)

@bp.route('/')
def macro_overlay_dashboard():
    analyzer = current_app.analyzers.get('macro_overlay')
    if not analyzer:
        return "Macro Overlay Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/macro_overlay.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)