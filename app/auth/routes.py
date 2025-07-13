from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_user, logout_user, login_required
from app import db, oauth # Import oauth
from app.models import User, Group
from . import bp
import functools

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

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
        
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/google/login')
def google_login():
    # Check if Google Client ID/Secret are configured
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google SSO is not configured. Please set Client ID and Secret in settings.', 'error')
        return redirect(url_for('auth.login'))

    # Redirect user to Google for authentication
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route('/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        userinfo = oauth.google.parse_id_token(token)
        
        # Check if userinfo contains email and name
        if 'email' not in userinfo:
            flash('Google login failed: Email not provided by Google.', 'error')
            return redirect(url_for('auth.login'))

        email = userinfo['email']
        username = userinfo.get('name', email.split('@')[0]) # Use name if available, else part of email
        
        user = User.query.filter_by(email=email).first()
        
        if user is None:
            # If user does not exist, create a new user.
            # Assign to a default group (e.g., 'Viewer') or prompt for group assignment later.
            # For simplicity, let's assign to 'Viewer' group if it exists, otherwise no group.
            viewer_group = Group.query.filter_by(name='Viewer').first()
            
            user = User(username=username, email=email, group=viewer_group)
            # No password for SSO users, but set a placeholder or handle appropriately if your model requires it.
            # For now, we'll assume password_hash can be null for SSO users or set a dummy value.
            # It's better to ensure your User model allows password_hash to be nullable if using SSO.
            # user.set_password(None) # Or set a random hash if nullable=False
            
            db.session.add(user)
            db.session.commit()
            flash(f'New user {username} created via Google SSO!', 'success')
        
        login_user(user)
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Google login failed: {e}', 'error')
        current_app.logger.error(f"Google SSO callback error: {e}")
        return redirect(url_for('auth.login'))

