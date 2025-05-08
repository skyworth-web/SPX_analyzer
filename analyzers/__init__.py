from .base import BaseAnalyzer
from .spread import SpreadAnalyzer
# from .bs_deviation import BSDeviationAnalyzer
# from .skew import SkewAnalyzer
# from .macro_overlay import MacroOverlayAnalyzer

def init_analyzers(app):
    """Initialize all analyzers and register with Flask app"""
    app.analyzers = {
        'spread': SpreadAnalyzer(),
        # 'bs_deviation': BSDeviationAnalyzer(),
        # 'skew': SkewAnalyzer(),
        # 'macro_overlay': MacroOverlayAnalyzer()
    }
    
    # Make analyzers available to templates
    @app.context_processor
    def inject_analyzers():
        return dict(analyzers=app.analyzers)