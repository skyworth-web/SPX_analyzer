from .base import BaseAnalyzer
from .spread import SpreadAnalyzer
from .bs_deviation import BSDeviationAnalyzer
from .skew import SkewAnalyzer
from .macro_overlay import MacroOverlayAnalyzer
from .iron_condor import IroncondorAnalyzer

def init_analyzers(app):
    """Initialize all analyzers and register with Flask app"""
    app.analyzers = {
        'spread': SpreadAnalyzer(),
        'bs_deviation': BSDeviationAnalyzer(),
        'skew': SkewAnalyzer(),
        'macro_overlay': MacroOverlayAnalyzer(),
        'iron_condor': IroncondorAnalyzer()
    }
    
    # Initialize each analyzer
    for analyzer in app.analyzers.values():
        if hasattr(analyzer, 'init_app'):
            analyzer.init_app(app)