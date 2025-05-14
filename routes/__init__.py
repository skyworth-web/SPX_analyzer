from flask import Blueprint, render_template

def create_blueprint():
    bp = Blueprint('main', __name__)

    @bp.route('/new-dashboard/')
    @bp.route('/new-dashboard/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @bp.route('/new-dashboard/analyzer-workspace')
    def analyzer_workspace():
        return render_template('analyzer_workspace.html')

    return bp

def init_routes(app):
    """Initialize all routes for the application"""
    app.register_blueprint(create_blueprint())
    
    # Register analyzer blueprints
    from .spread import bp as spread_bp
    from .bs_deviation import bp as bs_deviation_bp
    from .skew import bp as skew_bp
    from .macro_overlay import bp as macro_overlay_bp
    from .iron_condor import bp as iron_condor_bp
    from .short_vertical import bp as short_vertical_bp
    
    app.register_blueprint(spread_bp, url_prefix='/new-dashboard/spread')
    app.register_blueprint(bs_deviation_bp, url_prefix='/new-dashboard/bs-deviation')
    app.register_blueprint(skew_bp, url_prefix='/new-dashboard/skew')
    app.register_blueprint(macro_overlay_bp, url_prefix='/new-dashboard/macro-overlay')
    app.register_blueprint(iron_condor_bp, url_prefix='/new-dashboard/iron-condor')
    app.register_blueprint(short_vertical_bp, url_prefix='/new-dashboard/shortvertical')
