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
    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .scripts import bp as scripts_bp
    app.register_blueprint(scripts_bp, url_prefix='/scripts') # Changed this line

    from .hosts import bp as hosts_bp
    app.register_blueprint(hosts_bp)

    from app.pipelines import bp as pipelines_bp
    app.register_blueprint(pipelines_bp, url_prefix='/pipelines')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    # Register custom filters
    app.jinja_env.filters['distro_icon'] = get_distro_icon
    app.jinja_env.filters['distro_class'] = get_distro_class

    return app

# Add this function to your existing __init__.py

def get_distro_icon(distro):
    """Return appropriate icon for Linux distribution."""
    distro_icons = {
        'Ubuntu': 'fab fa-ubuntu',
        'Debian': 'fab fa-debian',
        'CentOS': 'fab fa-centos',
        'RHEL': 'fab fa-redhat',
        'Fedora': 'fab fa-fedora',
        'SUSE': 'fab fa-suse',
        'OpenSUSE': 'fab fa-suse',
        'Alpine': 'fas fa-mountain',
        'Arch': 'fab fa-arch-linux',
        'Manjaro': 'fas fa-leaf',
        'Mint': 'fab fa-mint',
        'Pop!_OS': 'fas fa-rocket',
        'Kali': 'fas fa-user-secret',
        'Rocky Linux': 'fas fa-mountain',
        'AlmaLinux': 'fas fa-server',
        'Amazon Linux': 'fab fa-aws',
        'Other': 'fas fa-server'
    }
    return distro_icons.get(distro, 'fas fa-server')

def get_distro_class(distro):
    """Return CSS class for distro styling."""
    if not distro:
        return 'distro-other'
    return f"distro-{distro.lower().replace(' ', '_').replace('!', '').replace('linux', '').strip('_')}"

# This import must be at the bottom to avoid circular dependencies
from app import models