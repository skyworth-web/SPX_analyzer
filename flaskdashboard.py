from flask import Flask
from models import db
from analyzers import init_analyzers

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Initialize database
    db.init_app(app)
    
    # Initialize analyzers first
    init_analyzers(app)
    
    # Initialize routes after analyzers
    from routes import init_routes
    init_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)