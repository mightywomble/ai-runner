# app/settings/__init__.py
from flask import Blueprint

bp = Blueprint('settings', __name__, template_folder='templates')

from . import routes