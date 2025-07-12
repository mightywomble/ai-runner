from flask import render_template, redirect, url_for, flash, jsonify, request
from . import bp
from app import db
from app.models import Script, Host
from config import Config
from github import Github, UnknownObjectException
import base64
import google.generativeai as genai
import openai
from app.utils import get_repo_scripts_recursive, get_script_icon

@bp.route('/')
def scripts_list():
    local_scripts = Script.query.order_by(Script.name).all()
    
    github_scripts = []
    app_config = Config.get_app_config() or {}
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if github_token and repo_name:
        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)
            github_scripts = get_repo_scripts_recursive(repo)
        except UnknownObjectException:
            flash(f"Repository '{repo_name}' not found or token is invalid.", "error")
        except Exception as e:
            flash(f"Could not connect to GitHub: {e}", "error")

    return render_template('scripts/scripts.html', 
                           title='Scripts', 
                           local_scripts=local_scripts, 
                           github_scripts=github_scripts)

@bp.route('/edit/<int:script_id>', methods=['GET', 'POST'])
def edit_script(script_id):
    script_to_edit = Script.query.get_or_404(script_id)
    if request.method == 'POST':
        script_to_edit.name = request.form['name']
        script_to_edit.content = request.form['content']
        script_to_edit.description = request.form.get('description')
        try:
            db.session.commit()
            flash(f'Script "{script_to_edit.name}" has been updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating script: {e}', 'error')
        return redirect(url_for('scripts.scripts_list'))
    
    return render_template('scripts/edit_script.html', title=f'Edit {script_to_edit.name}', script=script_to_edit)

@bp.route('/delete/<int:script_id>', methods=['POST'])
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
def push_to_github(script_id):
    app_config = Config.get_app_config() or {}
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if not github_token or not repo_name:
        flash("GitHub settings are not configured.", "error")
        return redirect(url_for('scripts.scripts_list'))

    script = Script.query.get_or_404(script_id)
    
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        dir_name = script.script_type.lower().replace(" ", "-")
        file_path = f"{dir_name}/{script.name}"
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
def get_github_script_content():
    data = request.get_json()
    path = data.get('path')
    
    app_config = Config.get_app_config() or {}
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
def analyze_script():
    data = request.get_json()
    script = data.get('script')
    ai_provider = data.get('ai_provider')
    if not script or not ai_provider: return jsonify({'error': 'Missing script or AI provider.'}), 400
    
    analysis_prompt = f"You are a helpful DevOps assistant. Analyze the following script. Use 'HEADING: ' to mark section titles for 'Summary', 'Dependencies', 'Expected Outcome', and 'Potential Issues'.\n\nScript:\n```\n{script}\n```"
    
    app_config = Config.get_app_config() or {}
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
