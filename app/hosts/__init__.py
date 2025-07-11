from flask import Blueprint

# The template_folder argument is removed.
bp = Blueprint('hosts', __name__)

from . import routes
