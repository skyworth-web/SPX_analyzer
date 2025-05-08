from flask import Blueprint

bp = Blueprint('skew', __name__)

@bp.route('/')
def skew_dashboard():
    return "Skew Analyzer Dashboard - Coming Soon"