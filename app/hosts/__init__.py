from flask import Blueprint

# Define the blueprint. Using 'bp' as the variable name is a common convention.
bp = Blueprint('hosts', __name__, template_folder='templates')

# Import the routes module *after* the blueprint has been defined.
# This makes the 'bp' object available for the routes to use.
from . import routes
