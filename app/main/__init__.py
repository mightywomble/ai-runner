from flask import Blueprint

bp = Blueprint('main', __name__)

# This import must be at the bottom to avoid circular dependencies
from app.main import routes
