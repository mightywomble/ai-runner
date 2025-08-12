from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from . import bp
from ..models import Script, Setting # MODIFIED: Added Setting model import
from .. import db
# from config import Config # MODIFIED: Removed unused import
from github import Github, UnknownObjectException
import base64
import google.generativeai as genai
import openai
from app.utils import get_repo_scripts_recursive, get_script_icon
from flask_login import login_required, current_user
import functools

# Helper decorator for permission checking
def permission_required(feature, access_level):
    def decorator(f):
        @login_required
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(feature, access_level):
                flash(f'You do not have {access_level} access to {feature}.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/save', methods=['POST'])
@login_required
@permission_required('scripts', 'full')
def save_script():
    try:
        data = request.get_json()
        if not data: return jsonify({'success': False, 'error': 'No data provided'}), 400
        name = data.get('name')
        content = data.get('content')
        script_type = data.get('script_type', 'Bash Script')
        if not name or not content: return jsonify({'success': False, 'error': 'Name and content are required'}), 400
        existing_script = Script.query.filter_by(name=name).first()
        if existing_script:
            existing_script.content = content
            existing_script.script_type = script_type
            message = f'Script "{name}" updated successfully.'
        else:
            script = Script(name=name, content=content, script_type=script_type)
            db.session.add(script)
            message = f'Script "{name}" saved successfully.'
        db.session.commit()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/')
@permission_required('scripts', 'view')
def scripts_list():
    local_scripts = Script.query.order_by(Script.name).all()
    return render_template('scripts/scripts.html', title='Scripts', local_scripts=local_scripts)

@bp.route('/github-scripts', methods=['GET'])
@login_required
@permission_required('scripts', 'view')
def get_github_scripts():
    github_scripts = []
    # MODIFIED: Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}
    
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if github_token and repo_name:
        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            github_scripts = get_repo_scripts_recursive(repo)
        except UnknownObjectException:
            return jsonify({'error': f"Repository '{repo_name}' not found or token is invalid."}), 404
        except Exception as e:
            return jsonify({'error': f"Could not connect to GitHub: {str(e)}"}), 500
    else:
        return jsonify({'message': 'GitHub settings are not configured.'}), 200

    return jsonify({'github_scripts': github_scripts})


@bp.route('/edit/<int:script_id>', methods=['GET', 'POST'])
@login_required
@permission_required('scripts', 'full')
def edit_script(script_id):
    # Handle creating a new script (script_id = 0)
    if script_id == 0:
        script_to_edit = Script(name='', content='', script_type='Bash Script', description='')
    else:
        script_to_edit = Script.query.get_or_404(script_id)
    if request.method == 'POST':
        script_to_edit.name = request.form['name']
        script_to_edit.content = request.form['content']
        script_to_edit.description = request.form.get('description')
        script_to_edit.script_type = request.form.get('script_type', 'Bash Script')
        try:
            # If script_id was 0, this is a new script, so add it to the session
            if script_id == 0:
                db.session.add(script_to_edit)
                flash(f'Script "{script_to_edit.name}" has been created.', 'success')
            else:
                flash(f'Script "{script_to_edit.name}" has been updated.', 'success')
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving script: {e}', 'error')
        return redirect(url_for('scripts.scripts_list'))
    # Set appropriate title based on whether this is a new script or existing script
    title = 'New Script' if script_id == 0 else f'Edit {script_to_edit.name}'
    return render_template('scripts/edit_script.html', title=title, script=script_to_edit, script_types=['Bash Command', 'Bash Script', 'Ansible Playbook', 'Python Script'])


@bp.route('/delete/<int:script_id>', methods=['POST'])
@login_required
@permission_required('scripts', 'full')
def delete_script(script_id):
    script_to_delete = Script.query.get_or_404(script_id)
    try:
        db.session.delete(script_to_delete)
        db.session.commit()
        flash(f'Script "{script_to_delete.name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting script: {e}', 'error')
    return redirect(url_for('scripts.scripts_list'))

@bp.route('/push-to-github/<int:script_id>', methods=['POST'])
@login_required
@permission_required('scripts', 'full')
def push_to_github(script_id):
    # MODIFIED: Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}

    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if not github_token or not repo_name:
        flash("GitHub settings are not configured.", "error")
        return redirect(url_for('scripts.scripts_list'))

    script = Script.query.get_or_404(script_id)
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        dir_name_map = {'Bash Command': 'bash-commands', 'Bash Script': 'bash-scripts', 'Ansible Playbook': 'ansible-playbooks', 'Python Script': 'python-scripts'}
        dir_name = dir_name_map.get(script.script_type, 'other-scripts')
        file_extension_map = {'Bash Command': '.sh', 'Bash Script': '.sh', 'Ansible Playbook': '.yml', 'Python Script': '.py'}
        file_extension = file_extension_map.get(script.script_type, '')
        file_path = f"{dir_name}/{script.name}{file_extension}"
        commit_message = f"Add/update script: {script.name}"
        try:
            contents = repo.get_contents(file_path, ref="dev")
            repo.update_file(contents.path, commit_message, script.content, contents.sha, branch="dev")
            flash(f'Script "{script.name}" updated in GitHub dev branch.', 'success')
        except UnknownObjectException:
            repo.create_file(file_path, commit_message, script.content, branch="dev")
            flash(f'Script "{script.name}" pushed to GitHub dev branch.', 'success')
    except Exception as e:
        flash(f"Failed to push to GitHub: {e}", "error")
    return redirect(url_for('scripts.scripts_list'))

@bp.route('/get-github-script-content', methods=['POST'])
@login_required
@permission_required('scripts', 'view')
def get_github_script_content():
    data = request.get_json()
    path = data.get('path')

    # MODIFIED: Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}

    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if not all([github_token, repo_name, path]):
        return jsonify({'error': 'Missing required data.'}), 400

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        file_content = repo.get_contents(path, ref="main")
        decoded_content = base64.b64decode(file_content.content).decode('utf-8')
        return jsonify({'content': decoded_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analyze-script', methods=['POST'])
@login_required
@permission_required('scripts', 'view')
def analyze_script():
    data = request.get_json()
    script = data.get('script')
    ai_provider = data.get('ai_provider')
    if not script or not ai_provider: return jsonify({'error': 'Missing script or AI provider.'}), 400
    
    # MODIFIED: Load settings from the database
    settings_list = Setting.query.all()
    app_config = {s.key: s.value for s in settings_list}
    
    analysis_prompt = f"You are a helpful DevOps assistant. Analyze the following script. Use 'HEADING: ' to mark section titles for 'Summary', 'Dependencies', 'Expected Outcome', and 'Potential Issues'.\n\nScript:\n```\n{script}\n```"
    try:
        if ai_provider == 'gemini':
            api_key = app_config.get('gemini_api_key')
            if not api_key: return jsonify({'error': 'Gemini API key is not configured.'}), 500
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(analysis_prompt)
            analysis = response.text
        else: # ChatGPT
            api_key = app_config.get('chatgpt_api_key')
            if not api_key: return jsonify({'error': 'ChatGPT API key is not configured.'}), 500
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": analysis_prompt}])
            analysis = response.choices[0].message.content
        return jsonify({'output': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500