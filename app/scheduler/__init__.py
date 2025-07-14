from flask import Blueprint

bp = Blueprint('scheduler', __name__)

from app.scheduler import routes
