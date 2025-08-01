from flask import render_template, request, jsonify
from flask_login import login_required, current_user # Import login_required and current_user
from . import bp
from config import Config
from app import db
from app.models import Host, Script, Setting # Import Setting model
import google.generativeai as genai
import openai
import paramiko
from github import Github, UnknownObjectException
import base64

@bp.route('/')
@bp.route('/index')
@login_required # Add this decorator to protect the route
def index():
    # You can now access current_user here if needed
    return render_template('index.html', title='Home')

@bp.route('/generate-script', methods=['POST'])
@login_required # Protect this route too
def generate_script():
    data = request.get_json()
    prompt = data.get('prompt')
    script_type = data.get('script_type')
    ai_provider = data.get('ai_provider')
    if not prompt or not script_type or not ai_provider: return jsonify({'error': 'Missing required data.'}), 400
    
    # Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}
    
    full_prompt = f"Generate a {script_type} script that does the following: {prompt}. The script should be complete, correct, and ready to run. Only output the code itself, with no explanation or markdown formatting."
    try:
        if ai_provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key: return jsonify({'error': 'Gemini API key is not configured in settings.'}), 500
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(full_prompt)
            script = response.text
        else:
            api_key = app_config.get('chatgpt_api_key')
            if not api_key: return jsonify({'error': 'ChatGPT API key is not configured in settings.'}), 500
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "You are a helpful assistant that only provides code."}, {"role": "user", "content": full_prompt}])
            script = response.choices[0].message.content
        return jsonify({'script': script})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dry-run', methods=['POST'])
@login_required # Protect this route
def dry_run():
    data = request.get_json()
    script = data.get('script')
    ai_provider = data.get('ai_provider')
    if not script or not ai_provider: return jsonify({'error': 'Missing script or AI provider.'}), 400
    
    # Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}

    dry_run_prompt = f"You are a helpful Linux assistant. Analyze the following script and explain what it will do when run on an Ubuntu server. Use 'HEADING: ' to mark section titles like 'Executive Summary', 'Script Breakdown', 'Expected Output', etc. Describe the expected output and any potential side effects or files that will be created or modified.\n\nScript:\n```\n{script}\n```"
    try:
        if ai_provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key: return jsonify({'error': 'Gemini API key is not configured in settings.'}), 500
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(dry_run_prompt)
            output = response.text
        else:
            api_key = app_config.get('chatgpt_api_key')
            if not api_key: return jsonify({'error': 'ChatGPT API key is not configured in settings.'}), 500
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": dry_run_prompt}])
            output = response.choices[0].message.content
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/get-hosts', methods=['GET'])
@login_required # Protect this route
def get_hosts():
    hosts = Host.query.all()
    return jsonify([{'id': host.id, 'name': host.name} for host in hosts])

@bp.route('/run-script', methods=['POST'])
@login_required # Protect this route
def run_script():
    data = request.get_json()
    script = data.get('script')
    host_ids = data.get('host_ids')
    use_sudo = data.get('use_sudo', False)
    if not script or not host_ids: return jsonify({'error': 'Missing script or host IDs.'}), 400
    sanitized_script = script.replace("'", "'\\''")
    command_to_run = f"sudo bash -c '{sanitized_script}'" if use_sudo else script
    results = []
    hosts = Host.query.filter(Host.id.in_(host_ids)).all()
    for host in hosts:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=host.ip_address, username=host.ssh_user, look_for_keys=True, timeout=10)
            stdin, stdout, stderr = client.exec_command(command_to_run)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            results.append({'host_name': host.name, 'success': not error, 'output': output, 'error': error})
            client.close()
        except Exception as e:
            results.append({'host_name': host.name, 'success': False, 'output': '', 'error': str(e)})
    return jsonify({'results': results})

@bp.route('/analyze-output', methods=['POST'])
@login_required # Protect this route
def analyze_output():
    data = request.get_json()
    script = data.get('script')
    output = data.get('output')
    error = data.get('error')
    ai_provider = data.get('ai_provider')
    if not script or not ai_provider: return jsonify({'error': 'Missing data for analysis.'}), 400
    if error:
        analysis_prompt = f"The following script failed to execute. Analyze the script and the error message to determine the cause and suggest troubleshooting steps. Use 'HEADING: ' to mark section titles.\n\nScript:\n```\n{script}\n```\n\nError:\n```\n{error}\n```"
    else:
        analysis_prompt = f"Analyze the output of the following script. Provide a summary of what the output means. Use 'HEADING: ' to mark section titles.\n\nScript:\n```\n{script}\n```\n\nOutput:\n```\n{output}\n```"
    
    # Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}

    try:
        if ai_provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key: return jsonify({'error': 'Gemini API key is not configured in settings.'}), 500
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(analysis_prompt)
            analysis = response.text
        else:
            api_key = app_config.get('chatgpt_api_key')
            if not api_key: return jsonify({'error': 'ChatGPT API key is not configured in settings.'}), 500
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": analysis_prompt}])
            analysis = response.choices[0].message.content
        return jsonify({'output': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/save-script', methods=['POST'])
@login_required # Protect this route
def save_script():
    data = request.get_json()
    script_content = data.get('content') # Changed from 'script_content' to 'content' for consistency with frontend
    script_name = data.get('name')       # Changed from 'script_name' to 'name' for consistency with frontend
    script_type = data.get('script_type') # Added this line to retrieve script_type
    
    if not script_content or not script_name or not script_type: # Validate script_type
        return jsonify({'success': False, 'error': 'Missing data (content, name, or script_type).'}), 400
    
    # Create new script with script_type
    new_script = Script(name=script_name, content=script_content, script_type=script_type) 
    db.session.add(new_script)
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Script "{script_name}" saved.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/test-ai-provider', methods=['POST'])
@login_required # Protect this route
def test_ai_provider():
    data = request.get_json()
    provider = data.get('provider')
    
    # Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}

    if not provider:
        return jsonify({'success': False, 'error': 'No provider specified.'}), 400

    try:
        if provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key:
                return jsonify({'success': False, 'error': 'Gemini API key not set in Settings.'}), 400
            genai.configure(api_key=api_key)
            genai.list_models()
        elif provider == 'chatgpt':
            api_key = app_config.get('chatgpt_api_key')
            if not api_key:
                return jsonify({'success': False, 'error': 'ChatGPT API key not set in Settings.'}), 400
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
        else:
            return jsonify({'success': False, 'error': 'Unknown provider.'}), 400
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
