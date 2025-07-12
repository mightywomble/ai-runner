from flask import render_template, flash, request, jsonify, redirect, url_for
from . import bp
from app import db
from app.models import Host, Script, Pipeline
from config import Config
from app.utils import get_repo_scripts_recursive, get_script_icon
from github import Github, UnknownObjectException
import yaml
import paramiko
import json
import google.generativeai as genai
import openai
import requests

def _get_ai_analysis(prompt_text, ai_provider=None):
    """Helper function to get analysis from the configured AI provider."""
    app_config = Config.get_app_config() or {}
    # Use the passed provider, or fall back to the config
    if not ai_provider:
        ai_provider = app_config.get('ai_provider', 'gemini')
    
    api_key = app_config.get(f'{ai_provider}_api_key')
    if not api_key: return {"error": f"{ai_provider.capitalize()} API key not configured."}
    try:
        if ai_provider == 'gemini':
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt_text)
            return {"output": response.text}
        else: # ChatGPT
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt_text}])
            return {"output": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

@bp.route('/')
def pipeline_canvas():
    hosts = Host.query.order_by(Host.name).all()
    local_scripts = Script.query.order_by(Script.name).all()
    saved_pipelines = Pipeline.query.order_by(Pipeline.name).all()
    
    github_scripts = []
    github_pipelines = []
    app_config = Config.get_app_config() or {}
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')

    if github_token and repo_name:
        try:
            g = Github(github_token)
            repo = g.get_repo(repo_name)

            def get_all_repo_contents(repo, path=""):
                """Recursively get all file contents from a repo."""
                contents = repo.get_contents(path)
                files = []
                for content_file in contents:
                    if content_file.type == "dir":
                        files.extend(get_all_repo_contents(repo, content_file.path))
                    else:
                        files.append(content_file)
                return files

            all_repo_contents = get_all_repo_contents(repo)

            for content_file in all_repo_contents:
                if content_file.path.startswith('pipelines/'):
                    github_pipelines.append({
                        'name': content_file.name,
                        'path': content_file.path
                    })
                else:
                    # It's a script, so try to get its content.
                    try:
                        content = content_file.decoded_content.decode('utf-8')
                        github_scripts.append({
                            'name': content_file.name,
                            'path': content_file.path,
                            'icon': get_script_icon(content_file.name),
                            'content': content
                        })
                    except (UnicodeDecodeError, Exception):
                        # Skip binary files or files with other decoding issues.
                        continue
        except Exception as e:
            flash(f"Could not get GitHub content: {e}", "error")

    notifications = { 'discord': bool(app_config.get('discord_webhook')), 'email': bool(app_config.get('email_server')) }

    return render_template('pipelines/pipelines.html', title='Pipeline Builder', hosts=hosts, local_scripts=local_scripts, github_scripts=github_scripts, saved_pipelines=saved_pipelines, github_pipelines=github_pipelines, notifications=notifications)

@bp.route('/save', methods=['POST'])
def save_pipeline():
    data = request.get_json()
    name = data.get('name')
    yaml_content = data.get('yaml')
    graph = data.get('graph')
    if not all([name, yaml_content, graph]): return jsonify({'success': False, 'error': 'Missing data.'}), 400
    
    # Check if a pipeline with this name already exists
    existing_pipeline = Pipeline.query.filter_by(name=name).first()
    if existing_pipeline:
        # Update existing pipeline
        existing_pipeline.yaml_content = yaml_content
        existing_pipeline.graph_json = json.dumps(graph)
        pipeline_id = existing_pipeline.id
        message = f'Pipeline "{name}" updated.'
    else:
        # Create new pipeline
        new_pipeline = Pipeline(name=name, yaml_content=yaml_content, graph_json=json.dumps(graph))
        db.session.add(new_pipeline)
        db.session.flush() # To get the ID before committing
        pipeline_id = new_pipeline.id
        message = f'Pipeline "{name}" saved.'

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': message, 'pipeline_id': pipeline_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/run/<int:pipeline_id>', methods=['POST'])
def run_pipeline(pipeline_id):
    data = request.get_json()
    use_sudo = data.get('use_sudo', False)
    ai_provider = data.get('ai_provider', 'gemini')
    
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    graph = json.loads(pipeline.graph_json)
    nodes = graph['nodes']
    connections = graph['connections']

    # --- Topological Sort to get correct execution order ---
    in_degree = {node_id: 0 for node_id in nodes}
    adj = {node_id: [] for node_id in nodes}
    for conn in connections:
        if conn['from'] in adj and conn['to'] in in_degree:
            adj[conn['from']].append(conn['to'])
            in_degree[conn['to']] += 1

    queue = [node_id for node_id in nodes if in_degree[node_id] == 0]
    sorted_order = []
    while queue:
        node_id = queue.pop(0)
        sorted_order.append(node_id)
        for neighbor_id in adj.get(node_id, []):
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)
    
    if len(sorted_order) != len(nodes):
        return jsonify({'results': [{'step_name': 'Pipeline Error', 'success': False, 'output': '', 'error': 'Pipeline has a cycle and cannot be run.'}]}), 400
    # --- End Topological Sort ---

    execution_results = []
    context = {} 
    
    # Find a default host to use if no explicit connection is made
    default_host_node_id = next((nid for nid, n in nodes.items() if n.get('type') == 'host'), None)
    default_host_node = nodes.get(default_host_node_id) if default_host_node_id else None

    for node_id in sorted_order:
        node = nodes[node_id]
        step_name = node['name']
        step_type = node['type']
        
        if step_type == 'host':
            continue # Hosts are targets, not executable steps

        if step_type == 'script':
            # Find an explicit host connection first
            explicit_connection = next((c for c in connections if c['to'] == node_id and nodes.get(c['from'], {}).get('type') == 'host'), None)
            host_node = nodes.get(explicit_connection['from']) if explicit_connection else None
            
            # If no explicit host, use the default one for the pipeline
            if not host_node:
                host_node = default_host_node

            if not host_node:
                execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': 'No host connected to this script, and no default host found in pipeline.'})
                continue
            
            target_host = Host.query.filter_by(name=host_node['name']).first()
            if not target_host:
                execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': f"Host '{host_node['name']}' not found in database."})
                continue

            script_content = node.get('content')
            if not script_content:
                execution_results.append({'step_name': step_name, 'success': True, 'output': 'No script content to run.', 'error': ''})
                continue
            
            context['last_script'] = script_content
            
            try:
                sanitized_script = script_content.replace("'", "'\\''")
                command = f"sudo bash -c '{sanitized_script}'" if use_sudo else f"bash -c '{sanitized_script}'"
                
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=target_host.ip_address, username=target_host.ssh_user, look_for_keys=True, timeout=10)
                
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                exit_code = stdout.channel.recv_exit_status()
                client.close()
                
                context['last_output'] = output
                context['last_error'] = error
                execution_results.append({'step_name': step_name, 'success': exit_code == 0, 'output': output, 'error': error})
            except Exception as e:
                context['last_error'] = str(e)
                execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': str(e)})

        elif step_type == 'action':
            if node['name'] == 'AI Analysis':
                prompt = f"Analyze the output of the previous script. Provide a summary, breakdown, and troubleshooting suggestions.\n\nScript:\n```\n{context.get('last_script', 'N/A')}\n```\n\nOutput:\n```\n{context.get('last_output', '')}\n```\n\nError:\n```\n{context.get('last_error', '')}\n```"
                analysis = _get_ai_analysis(prompt, ai_provider)
                context['last_analysis'] = analysis.get('output', '')
                execution_results.append({'step_name': step_name, 'success': not analysis.get('error'), 'output': analysis.get('output', ''), 'error': analysis.get('error', '')})
            
            elif node['name'] == 'Notify Discord':
                app_config = Config.get_app_config() or {}
                webhook_url = app_config.get('discord_webhook')
                if not webhook_url:
                    execution_results.append({'step_name': step_name, 'success': False, 'output': '', 'error': 'Discord webhook not configured.'})
                    continue
                
                message = (f"**Pipeline Execution Report**\n\n"
                           f"**Last Script:**\n```bash\n{context.get('last_script', 'N/A')}\n```\n"
                           f"**Output:**\n```\n{context.get('last_output', 'N/A')}\n```\n"
                           f"**AI Analysis:**\n{context.get('last_analysis', 'N/A')}")
                
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
    if not yaml_content or not ai_provider: return jsonify({'error': 'Missing YAML content or AI provider.'}), 400
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
        else:
            api_key = app_config.get('chatgpt_api_key')
            if not api_key: return jsonify({'error': 'ChatGPT API key is not configured.'}), 500
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": analysis_prompt}])
            analysis = response.choices[0].message.content
        return jsonify({'output': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/load/<int:pipeline_id>', methods=['GET'])
def load_pipeline(pipeline_id):
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    return jsonify({
        'name': pipeline.name,
        'yaml': pipeline.yaml_content,
        'graph': json.loads(pipeline.graph_json)
    })

@bp.route('/delete/<int:pipeline_id>', methods=['POST'])
def delete_pipeline(pipeline_id):
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    try:
        db.session.delete(pipeline)
        db.session.commit()
        flash(f'Pipeline "{pipeline.name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting pipeline: {e}', 'error')
    return redirect(url_for('pipelines.pipeline_canvas'))

@bp.route('/push-to-github/<int:pipeline_id>', methods=['POST'])
def push_pipeline_to_github(pipeline_id):
    app_config = Config.get_app_config() or {}
    github_token = app_config.get('github_api_key')
    repo_name = app_config.get('github_repo')
    if not github_token or not repo_name:
        flash("GitHub settings are not configured.", "error")
        return redirect(url_for('pipelines.pipeline_canvas'))
    
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        file_path = f"pipelines/{pipeline.name}.yml"
        commit_message = f"Add/update pipeline: {pipeline.name}"
        
        try:
            contents = repo.get_contents(file_path, ref="dev")
            repo.update_file(contents.path, commit_message, pipeline.yaml_content, contents.sha, branch="dev")
            flash(f'Pipeline "{pipeline.name}" updated in GitHub dev branch.', 'success')
        except UnknownObjectException:
            repo.create_file(file_path, commit_message, pipeline.yaml_content, branch="dev")
            flash(f'Pipeline "{pipeline.name}" pushed to GitHub dev branch.', 'success')
    except Exception as e:
        flash(f"Failed to push to GitHub: {e}", "error")
    return redirect(url_for('pipelines.pipeline_canvas'))

@bp.route('/pipelines/<int:pipeline_id>/update', methods=['POST'])
def update_pipeline(pipeline_id):
    data = request.get_json()
    name = data.get('name')
    yaml_content = data.get('yaml')
    graph = data.get('graph')
    
    if not all([name, yaml_content, graph]):
        return jsonify({'success': False, 'error': 'Missing data.'}), 400
    
    try:
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        pipeline.name = name
        pipeline.yaml_content = yaml_content
        pipeline.graph_json = json.dumps(graph)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Pipeline "{name}" updated.', 'pipeline_id': pipeline_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
