from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Setting
import functools
from . import bp

# Helper decorator for permission checking
def permission_required(feature, access_level):
    def decorator(f):
        @login_required
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(feature, access_level):
                flash(f'You do not have {access_level} access to {feature}.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('settings', 'view') # User must have at least 'view' access
def settings_page():
    """
    Handles both displaying and saving application settings from the database.
    """
    if request.method == 'POST':
        # Explicitly check for 'full' access to save settings
        if not current_user.can('settings', 'full'):
            flash('You do not have permission to save settings.', 'error')
            return redirect(url_for('settings.settings_page'))

        settings_keys = [
            'gemini_api_key', 'chatgpt_api_key', 'github_api_key', 'github_repo',
            'google_client_id', 'google_client_secret', 'discord_webhook',
            'smtp_server', 'smtp_port', 'smtp_use_tls', 'smtp_sender_email',
            'smtp_username', 'smtp_password', 'enable_login_debug'
        ]
        try:
            for key in settings_keys:
                if key in ['smtp_use_tls', 'enable_login_debug']:
                    value = 'true' if key in request.form else 'false'
                else:
                    value = request.form.get(key, '')

                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    new_setting = Setting(key=key, value=value)
                    db.session.add(new_setting)
            
            db.session.commit()
            
            # Update the live app config for immediate changes (e.g., for OAuth)
            current_app.config['GOOGLE_CLIENT_ID'] = request.form.get('google_client_id')
            current_app.config['GOOGLE_CLIENT_SECRET'] = request.form.get('google_client_secret')
            current_app.config['ENABLE_LOGIN_DEBUG'] = 'true' if 'enable_login_debug' in request.form else 'false'
            
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving settings: {e}', 'error')
        
        return redirect(url_for('settings.settings_page'))

    # This is the display logic for GET requests
    settings_from_db = Setting.query.all()
    app_config = {setting.key: setting.value for setting in settings_from_db}
    
    # Ensure booleans are correctly interpreted for checkboxes
    app_config['enable_login_debug'] = app_config.get('enable_login_debug') == 'true'
    app_config['smtp_use_tls'] = app_config.get('smtp_use_tls') == 'true'

    return render_template('settings/settings.html', title='Application Settings', app_config=app_config)
