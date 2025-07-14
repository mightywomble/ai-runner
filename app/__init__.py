from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
oauth = OAuth()

# Configure the scheduler to use the database as its job store
jobstores = {
    'default': SQLAlchemyJobStore(url=Config.SQLALCHEMY_DATABASE_URI)
}
# Renamed 'scheduler' to 'bg_scheduler' to avoid name conflicts
bg_scheduler = BackgroundScheduler(jobstores=jobstores, daemon=True)

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

def resync_scheduler_jobs(app):
    """
    Clears existing jobs and re-adds all enabled jobs from the database.
    This ensures the scheduler is in sync with the DB on app startup.
    """
    with app.app_context():
        from app.models import ScheduledJob
        
        # Use the renamed scheduler object
        bg_scheduler.remove_all_jobs()
        jobs = ScheduledJob.query.filter_by(is_enabled=True).all()
        for job in jobs:
            try:
                # Use the renamed scheduler object and pass the task as a string
                bg_scheduler.add_job(
                    id=str(job.id),
                    func='app.scheduler.tasks:pipeline_task', # Pass as string to avoid pickling issues
                    args=[job.id],
                    trigger=CronTrigger.from_crontab(job.cron_string),
                    replace_existing=True,
                    misfire_grace_time=3600 # Grace time of 1 hour for missed jobs
                )
            except Exception as e:
                print(f"Error adding job {job.id} to scheduler: {e}")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    oauth.init_app(app)

    # Initialize and start the scheduler
    # Use the renamed scheduler object
    if not bg_scheduler.running:
        bg_scheduler.start()
        # Resync jobs from DB after scheduler starts
        resync_scheduler_jobs(app)


    # User loader function for Flask-Login
    from app.models import User
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Configure Google OAuth
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
        jwks_uri='https://www.googleapis.com/oauth2/v3/certs'
    )

    # Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from .hosts import bp as hosts_bp
    app.register_blueprint(hosts_bp, url_prefix='/hosts')

    from .scripts import bp as scripts_bp
    app.register_blueprint(scripts_bp, url_prefix='/scripts')

    from .pipelines import bp as pipelines_bp
    app.register_blueprint(pipelines_bp, url_prefix='/pipelines')

    from .settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from .backup import bp as backup_bp
    app.register_blueprint(backup_bp, url_prefix='/backup')

    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .scheduler import bp as scheduler_bp
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')


    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    # Register custom filters
    app.jinja_env.filters['distro_icon'] = get_distro_icon
    app.jinja_env.filters['distro_class'] = get_distro_class

    return app

# This import must be at the bottom to avoid circular dependencies
from app import models
