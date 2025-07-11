# app/scripts/__init__.py
from flask import Blueprint

bp = Blueprint('scripts', __name__, template_folder='templates')

from . import routes
