from flask import render_template, flash
from . import bp
from app.models import Host, Script
from config import Config
from app.utils import get_repo_scripts_recursive
from github import Github, UnknownObjectException

@bp.route('/')
def pipeline_canvas():
    # Get all hosts from the database
    hosts = Host.query.order_by(Host.name).all()

    # Get all locally saved scripts from the database
    local_scripts = Script.query.order_by(Script.name).all()

    # Get all scripts from the configured GitHub repository
    github_scripts = []
    app_config = Config.get_app_config() or {}
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if github_token and repo_name:
        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            github_scripts = get_repo_scripts_recursive(repo)
        except Exception as e:
            flash(f"Could not get GitHub scripts for pipeline builder: {e}", "error")

    # Check which notification options are configured in settings
    notifications = {
        'discord': bool(app_config.get('discord_webhook')),
        # Assuming you might add email settings later
        'email': bool(app_config.get('email_server')) 
    }

    # Pass all the data to the template
    return render_template('pipelines/pipelines.html',
                           title='Pipeline Builder',
                           hosts=hosts,
                           local_scripts=local_scripts,
                           github_scripts=github_scripts,
                           notifications=notifications)
