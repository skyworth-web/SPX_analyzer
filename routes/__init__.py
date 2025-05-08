from flask import Blueprint

def create_blueprint():
    bp = Blueprint('main', __name__)
    
    @bp.route('/')
    @bp.route('/dashboard')
    def dashboard():
        from flask import render_template, current_app
        from models import SPXSpot
        from datetime import datetime
        
        try:
            spot = SPXSpot.query.order_by(SPXSpot.timestamp.desc()).first()
            return render_template('index.html',
                                spot_price=spot.price if spot else None,
                                analyzers=current_app.analyzers,
                                current_app=current_app)
        except Exception as e:
            current_app.logger.error(f"Dashboard error: {str(e)}")
            return render_template('index.html',
                                error=str(e),
                                current_app=current_app)
    
    return bp

def init_routes(app):
    """Initialize all routes for the application"""
    # Register main blueprint
    app.register_blueprint(create_blueprint())
    
    # Register analyzer blueprints
    from .spread import bp as spread_bp
    from .bs_deviation import bp as bs_deviation_bp
    from .skew import bp as skew_bp
    from .macro_overlay import bp as macro_overlay_bp
    
    app.register_blueprint(spread_bp, url_prefix='/spread')
    app.register_blueprint(bs_deviation_bp, url_prefix='/bs-deviation')
    app.register_blueprint(skew_bp, url_prefix='/skew')
    app.register_blueprint(macro_overlay_bp, url_prefix='/macro-overlay')