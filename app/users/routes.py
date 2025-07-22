from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Group
from . import bp
import json # For handling permissions JSON
import functools # Import functools for @functools.wraps

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
@bp.route('/list') # Both /users/ and /users/list will show the list
@login_required
@permission_required('users', 'view') # Requires 'view' access to 'users' feature
def users_list():
    users = User.query.order_by(User.username).all()
    groups = Group.query.order_by(Group.name).all()
    return render_template('users/users_list.html', title='User & Group Management', users=users, groups=groups)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@permission_required('users', 'full') # Requires 'full' access to 'users' feature
def add_user():
    groups = Group.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        group_id = request.form.get('group_id')

        if not username or not email or not password:
            flash('Username, email, and password are required.', 'error')
            return redirect(url_for('users.add_user'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('users.add_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('users.add_user'))

        user = User(username=username, email=email, group_id=group_id if group_id else None)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
            flash(f'User "{username}" added successfully.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {e}', 'error')
    return render_template('users/add_user.html', title='Add User', groups=groups)

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('users', 'full') # Requires 'full' access to 'users' feature
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    groups = Group.query.all()
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        new_password = request.form.get('password')
        user.group_id = request.form.get('group_id') if request.form.get('group_id') else None

        if new_password:
            user.set_password(new_password)
        
        try:
            db.session.commit()
            flash(f'User "{user.username}" updated successfully.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {e}', 'error')
    return render_template('users/edit_user.html', title='Edit User', user=user, groups=groups)

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('users', 'full') # Requires 'full' access to 'users' feature
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == current_user.username:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for('users.users_list'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{user.username}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {e}', 'error')
    return redirect(url_for('users.users_list'))

@bp.route('/users/<int:user_id>/generate_api_key', methods=['POST'])
@login_required
@permission_required('users', 'full')
def generate_api_key(user_id):
    user = User.query.get_or_404(user_id)
    new_key = user.generate_api_key()
    db.session.commit()
    groups = Group.query.all()
    # Re-render the edit page, passing the new key to be displayed in a modal
    return render_template('users/edit_user.html', 
                           title='Edit User', 
                           user=user, 
                           groups=groups,
                           new_api_key=new_key)

@bp.route('/users/<int:user_id>/revoke_api_key', methods=['POST'])
@login_required
@permission_required('users', 'full')
def revoke_api_key(user_id):
    user = User.query.get_or_404(user_id)
    user.revoke_api_key()
    db.session.commit()
    flash(f'API Key for {user.username} has been revoked.', 'info')
    return redirect(url_for('users.edit_user', user_id=user_id))

@bp.route('/groups/add', methods=['GET', 'POST'])
@login_required
@permission_required('groups', 'full') # Requires 'full' access to 'groups' feature
def add_group():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Group name is required.', 'error')
            return redirect(url_for('users.add_group'))
        
        if Group.query.filter_by(name=name).first():
            flash('Group name already exists.', 'error')
            return redirect(url_for('users.add_group'))

        new_group = Group(name=name)
        
        permissions_data = {}
        features = ['hosts', 'scripts', 'pipelines', 'users', 'settings', 'groups']
        for feature in features:
            permissions_data[feature] = request.form.get(f'permission_{feature}', 'none')
        new_group.set_permissions(permissions_data)

        db.session.add(new_group)
        try:
            db.session.commit()
            flash(f'Group "{name}" added successfully.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding group: {e}', 'error')
    
    features_access_levels = {
        'hosts': ['none', 'view', 'full'],
        'scripts': ['none', 'view', 'full'],
        'pipelines': ['none', 'view', 'full'],
        'users': ['none', 'view', 'full'],
        'settings': ['none', 'view', 'full'],
        'groups': ['none', 'view', 'full']
    }
    return render_template('users/add_group.html', title='Add Group', features_access_levels=features_access_levels)


@bp.route('/groups/edit/<int:group_id>', methods=['GET', 'POST'])
@login_required
@permission_required('groups', 'full')
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    if request.method == 'POST':
        group.name = request.form.get('name')
        if not group.name:
            flash('Group name is required.', 'error')
            return redirect(url_for('users.edit_group', group_id=group.id))

        permissions_data = {}
        features = ['hosts', 'scripts', 'pipelines', 'users', 'settings', 'groups']
        for feature in features:
            permissions_data[feature] = request.form.get(f'permission_{feature}', 'none')
        group.set_permissions(permissions_data)

        try:
            db.session.commit()
            flash(f'Group "{group.name}" updated successfully.', 'success')
            return redirect(url_for('users.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating group: {e}', 'error')
    
    features_access_levels = {
        'hosts': ['none', 'view', 'full'],
        'scripts': ['none', 'view', 'full'],
        'pipelines': ['none', 'view', 'full'],
        'users': ['none', 'view', 'full'],
        'settings': ['none', 'view', 'full'],
        'groups': ['none', 'view', 'full']
    }
    current_permissions = group.get_permissions()
    return render_template('users/edit_group.html', 
                           title='Edit Group', 
                           group=group, 
                           features_access_levels=features_access_levels,
                           current_permissions=current_permissions)

@bp.route('/groups/delete/<int:group_id>', methods=['POST'])
@login_required
@permission_required('groups', 'full')
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    if group.users.count() > 0:
        flash(f"Cannot delete group '{group.name}' because it still has users assigned.", "error")
        return redirect(url_for('users.users_list'))
    try:
        db.session.delete(group)
        db.session.commit()
        flash(f'Group "{group.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting group: {e}', 'error')
    return redirect(url_for('users.users_list'))
