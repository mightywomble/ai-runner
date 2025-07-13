from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import Group
from config import Config
import functools
from . import bp # Added this line to import the blueprint

# Helper decorator for permission checking
def permission_required(feature, access_level):
    def decorator(f):
        @login_required
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(feature, access_level):
                flash(f'You do not have {access_level} access to {feature}.', 'error')
                return redirect(url_for('main.index')) # Redirect to home or an unauthorized page
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/')
@bp.route('/settings')
@login_required
@permission_required('settings', 'view') # Requires 'view' access to 'settings' feature
def settings_page():
    app_config = Config.get_app_config() # This gets settings from config.yaml
    return render_template('settings/settings.html', title='Application Settings', app_config=app_config)

@bp.route('/settings/save', methods=['POST'])
@login_required
@permission_required('settings', 'full') # Requires 'full' access to 'settings' feature
def save_settings():
    # Get current settings from config.yaml
    current_settings = Config.get_app_config()
    
    # Update with form data
    current_settings['github_api_key'] = request.form.get('github_api_key')
    current_settings['github_repo'] = request.form.get('github_repo')
    current_settings['gemini_api_key'] = request.form.get('gemini_api_key')
    current_settings['chatgpt_api_key'] = request.form.get('chatgpt_api_key')
    current_settings['discord_webhook'] = request.form.get('discord_webhook')
    current_settings['email_server'] = request.form.get('email_server') # Assuming this is a simple string for now

    # Add Google OAuth settings
    current_settings['google_client_id'] = request.form.get('google_client_id')
    current_settings['google_client_secret'] = request.form.get('google_client_secret')

    # Add new setting for login debug
    current_settings['enable_login_debug'] = 'on' == request.form.get('enable_login_debug') # Checkbox value is 'on' if checked

    try:
        Config.save_app_config(current_settings) # Save updated settings to config.yaml
        # Re-load config into app.config for immediate use without restarting
        # This is important for Authlib to pick up new client IDs/secrets
        from flask import current_app
        current_app.config['GOOGLE_CLIENT_ID'] = current_settings['google_client_id']
        current_app.config['GOOGLE_CLIENT_SECRET'] = current_settings['google_client_secret']
        current_app.config['ENABLE_LOGIN_DEBUG'] = current_settings['enable_login_debug'] # Update app.config for immediate use
        
        flash('Settings saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving settings: {e}', 'error')
    
    return redirect(url_for('settings.settings_page'))
