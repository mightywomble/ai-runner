from flask import Blueprint

bp = Blueprint('api', __name__)

# Import routes for docs and the actual endpoints
from app.api import routes, endpoints
