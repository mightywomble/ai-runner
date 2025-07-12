from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.hosts import bp as hosts_bp
    app.register_blueprint(hosts_bp, url_prefix='/hosts')

    from app.scripts import bp as scripts_bp
    app.register_blueprint(scripts_bp, url_prefix='/scripts')
    
    from app.pipelines import bp as pipelines_bp
    app.register_blueprint(pipelines_bp, url_prefix='/pipelines')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app

# This import must be at the bottom to avoid circular dependencies
from app import models
