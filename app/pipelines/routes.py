from flask import render_template, flash, request, jsonify
from . import bp
from app import db
from app.models import Host, Script, Pipeline
from config import Config
from app.utils import get_repo_scripts_recursive
from github import Github, UnknownObjectException
import yaml
import paramiko
import json
import google.generativeai as genai
import openai
import requests

def _get_ai_analysis(prompt_text):
    """Helper function to get analysis from the configured AI provider."""
    app_config = Config.get_app_config() or {}
    ai_provider = app_config.get('ai_provider', 'gemini') # Default to gemini
    api_key = app_config.get(f'{ai_provider}_api_key')

    if not api_key:
        return {"error": f"{ai_provider.capitalize()} API key not configured."}

    try:
        if ai_provider == 'gemini':
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt_text)
            return {"output": response.text}
        else: # ChatGPT
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_text}]
            )
            return {"output": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

@bp.route('/')
def pipeline_canvas():
    hosts = Host.query.order_by(Host.name).all()
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
        except Exception as e:
            flash(f"Could not get GitHub scripts for pipeline builder: {e}", "error")

    notifications = { 'discord': bool(app_config.get('discord_webhook')), 'email': bool(app_config.get('email_server')) }

    return render_template('pipelines/pipelines.html', title='Pipeline Builder', hosts=hosts, local_scripts=local_scripts, github_scripts=github_scripts, notifications=notifications)

@bp.route('/save', methods=['POST'])
def save_pipeline():
    data = request.get_json()
    name = data.get('name')
    yaml_content = data.get('yaml')
    graph = data.get('graph')

    if not all([name, yaml_content, graph]):
        return jsonify({'success': False, 'error': 'Missing data.'}), 400
    
    if Pipeline.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': f'A pipeline named "{name}" already exists.'}), 400

    new_pipeline = Pipeline(name=name, yaml_content=yaml_content, graph_json=json.dumps(graph))
    db.session.add(new_pipeline)
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Pipeline "{name}" saved.', 'pipeline_id': new_pipeline.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/run/<int:pipeline_id>', methods=['POST'])
def run_pipeline(pipeline_id):
    data = request.get_json()
    use_sudo = data.get('use_sudo', False)
    
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    graph = json.loads(pipeline.graph_json)
    
    # A more robust execution engine
    execution_results = []
    context = {} # To pass data between steps

    # Simple sequential execution for now
    for node_id, node in graph['nodes'].items():
        step_name = node['name']
        step_type = node['type']
        
        if step_type == 'host':
            continue

        if step_type == 'script':
            connection = next((c for c in graph['connections'] if c['to'] == node_id), None)
            host_node_id = connection['from'] if connection else None
            host_node = graph['nodes'].get(host_node_id) if host_node_id else None
            
            if not host_node:
                execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': 'No host connected.'})
                continue
            
            target_host = Host.query.filter_by(name=host_node['name']).first()
            script_content = node.get('content')
            context['last_script'] = script_content
            
            try:
                sanitized_script = script_content.replace("'", "'\\''")
                command = f"sudo bash -c '{sanitized_script}'" if use_sudo else script_content
                
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=target_host.ip_address, username=target_host.ssh_user, look_for_keys=True, timeout=10)
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                client.close()
                
                context['last_output'] = output
                context['last_error'] = error
                execution_results.append({'step_name': step_name, 'success': not error, 'output': output, 'error': error})
            except Exception as e:
                context['last_error'] = str(e)
                execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': str(e)})

        elif step_type == 'action':
            if node['name'] == 'AI Analysis':
                prompt = f"Analyze the output of the previous script. Provide a summary, breakdown, and troubleshooting suggestions.\n\nScript:\n```\n{context.get('last_script', 'N/A')}\n```\n\nOutput:\n```\n{context.get('last_output', '')}\n```\n\nError:\n```\n{context.get('last_error', '')}\n```"
                analysis = _get_ai_analysis(prompt)
                context['last_analysis'] = analysis.get('output', '')
                execution_results.append({'step_name': step_name, 'success': not analysis.get('error'), 'output': analysis.get('output', ''), 'error': analysis.get('error', '')})
            
            elif node['name'] == 'Notify Discord':
                app_config = Config.get_app_config() or {}
                webhook_url = app_config.get('discord_webhook')
                if not webhook_url:
                    execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': 'Discord webhook not configured.'})
                    continue
                
                message = (
                    f"**Pipeline Execution Report**\n\n"
                    f"**Script:**\n```bash\n{context.get('last_script', 'N/A')}\n```\n"
                    f"**Output:**\n```\n{context.get('last_output', 'N/A')}\n```\n"
                    f"**AI Analysis:**\n{context.get('last_analysis', 'N/A')}"
                )
                
                try:
                    requests.post(webhook_url, json={'content': message[:2000]}, timeout=5)
                    execution_results.append({'step_name': step_name, 'success': True, 'output': 'Discord notification sent.', 'error': ''})
                except Exception as e:
                    execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': str(e)})
    
    return jsonify({'results': execution_results})

@bp.route('/dry-run-yaml', methods=['POST'])
def dry_run_yaml():
    data = request.get_json()
    yaml_content = data.get('yaml')
    ai_provider = data.get('ai_provider')

    if not yaml_content or not ai_provider:
        return jsonify({'error': 'Missing YAML content or AI provider.'}), 400

    app_config = Config.get_app_config() or {}
    analysis_prompt = f"You are a helpful DevOps assistant. Analyze the following pipeline YAML. Explain what the pipeline does, what each job is responsible for, and point out any potential issues or improvements. Use 'HEADING: ' to mark section titles.\n\nYAML:\n```yaml\n{yaml_content}\n```"
    
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
