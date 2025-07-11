# app/scripts/routes.py
from flask import jsonify
from . import bp

@bp.route('/')
def scripts_list():
    # This is a placeholder. You would create a template for this.
    return jsonify(message="Scripts route is working")