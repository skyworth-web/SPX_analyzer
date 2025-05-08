from flask import Blueprint, current_app
from models import SPXSpot  # Absolute import
from datetime import datetime

def create_blueprint():
    """Create and configure the main Blueprint"""
    bp = Blueprint('main', __name__)

    @bp.route('/')
    @bp.route('/dashboard')
    def dashboard():
        """Main dashboard view"""
        try:
            spot = SPXSpot.query.order_by(SPXSpot.timestamp.desc()).first()
            return current_app.response_class(
                response=f"SPX Price: {spot.price if spot else 'N/A'}",
                status=200
            )
        except Exception as e:
            current_app.logger.error(f"Dashboard error: {str(e)}")
            return current_app.response_class(
                response=f"Error: {str(e)}",
                status=500
            )

    return bp

def init_routes(app):
    """Initialize all routes for the application"""
    # Register main blueprint
    app.register_blueprint(create_blueprint())
    
    # Register analyzer blueprints
    from .spread import bp as spread_bp
    app.register_blueprint(spread_bp, url_prefix='/spread')