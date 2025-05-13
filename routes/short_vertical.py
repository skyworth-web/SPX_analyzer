from flask import Blueprint, render_template, current_app

bp = Blueprint('short_vertical', __name__)

@bp.route('/')
def short_vertical_dashboard():
    analyzer = current_app.analyzers.get('short_vertical')
    if not analyzer:
        return "Macro Overlay Analyzer not initialized", 500
        
    results = analyzer.get_latest_results()
    
    return render_template('analyzers/short_vertical.html',
                         analyzer=analyzer,
                         results=results,
                         current_app=current_app)