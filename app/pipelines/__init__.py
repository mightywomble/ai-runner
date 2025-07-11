# app/pipelines/__init__.py
from flask import Blueprint

bp = Blueprint('pipelines', __name__, template_folder='templates')

from . import routes