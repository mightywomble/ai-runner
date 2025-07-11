# app/settings/routes.py
from flask import render_template, request, redirect, url_for, flash
from config import Config
from . import bp

@bp.route('/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        Config.save_app_config(form_data)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings.settings'))
        
    app_config = Config.get_app_config()
    return render_template('settings.html', title='Settings', config=app_config)