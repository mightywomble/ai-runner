# app/pipelines/routes.py
from flask import render_template
from . import bp

@bp.route('/')
def pipeline_canvas():
    return render_template('pipelines.html', title='Pipeline Builder')