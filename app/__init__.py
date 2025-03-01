from flask import Flask
from .config import Config
from .db import mongo

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='templates')
    app.config.from_object(Config)
    
    # Initialize the MongoDB connection
    mongo.init_app(app)
    
    # Register Blueprints
    from .routes.auth import auth_bp
    from .routes.diary import diary_bp
    from .routes.chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(diary_bp)
    app.register_blueprint(chat_bp)
    
    return app
