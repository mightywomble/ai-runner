from flask import render_template, request, redirect, url_for, flash, jsonify
from config import Config
from . import bp
import requests
import json

@bp.route('/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Get existing config to preserve keys not in the form
        app_config = Config.get_app_config() or {}
        
        # Filter out empty password fields to avoid saving blank values over existing ones
        form_data = {key: value for key, value in request.form.items() if value}
        app_config.update(form_data)

        Config.save_app_config(app_config)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings.settings'))
        
    app_config = Config.get_app_config()
    
    # Ensure app_config is a dictionary, even if the yaml file is empty
    if app_config is None:
        app_config = {}
        
    return render_template('settings/settings.html', title='Settings', config=app_config)

@bp.route('/test-discord', methods=['POST'])
def test_discord():
    data = request.get_json()
    webhook_url = data.get('webhook_url')

    if not webhook_url:
        return jsonify({'success': False, 'error': 'Webhook URL is missing.'}), 400

    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({'content': 'This is a test message from AI Ops Runner.'})

    try:
        response = requests.post(webhook_url, data=payload, headers=headers, timeout=5)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return jsonify({'success': True})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': str(e)})
