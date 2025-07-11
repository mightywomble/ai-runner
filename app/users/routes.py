# app/users/routes.py
from flask import render_template
from . import bp

@bp.route('/')
def user_management():
    return render_template('users.html', title='User Management')