from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import json
# Import all necessary models and utility functions
from app.models import User, Host, Pipeline, Script, Setting 
from app.utils import get_ai_analysis, execute_ssh_command, send_to_discord

# Create a new Blueprint for the Zabbix API endpoint
zabbix_bp = Blueprint('zabbix_api', __name__)

# --- API Key Authentication Decorator ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key_header = request.headers.get('X-API-Key')
        if not api_key_header:
            return jsonify({'error': 'Authentication failed: Invalid or missing API key'}), 401
        api_key = api_key_header.strip()
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Authentication failed: Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


# --- The Zabbix Webhook Endpoint ---
@zabbix_bp.route('/trigger', methods=['POST'])
@require_api_key
def trigger_from_zabbix():
    """
    Receives an alert from Zabbix, finds the corresponding host and pipeline,
    executes all steps in the pipeline, and sends notifications.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    hostname_from_zabbix = data.get('hostname')
    pipeline_id = data.get('pipeline_id')
    trigger_name = data.get('trigger_name', 'N/A')
    
    if not hostname_from_zabbix or not pipeline_id:
        return jsonify({'error': 'Payload must contain "hostname" and "pipeline_id"'}), 400

    host = Host.query.filter_by(name=hostname_from_zabbix).first()
    if not host:
        current_app.logger.error(f"Pipeline trigger failed: Host '{hostname_from_zabbix}' not found.")
        return jsonify({'error': f'Host "{hostname_from_zabbix}" not found'}), 404

    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline:
        current_app.logger.error(f"Pipeline trigger failed: Pipeline ID '{pipeline_id}' not found.")
        return jsonify({'error': f'Pipeline ID "{pipeline_id}" not found'}), 404

    current_app.logger.info(f"Executing Pipeline '{pipeline.name}' on Host '{host.name}' from Zabbix trigger '{trigger_name}'.")

    # --- Full Pipeline Execution Engine ---
    
    # Context dictionary to hold results from each step
    pipeline_context = {
        "script_outputs": [],
        "ai_analysis": "",
        "errors": []
    }

    try:
        pipeline_data = json.loads(pipeline.definition) if pipeline.definition else {}
        if not (isinstance(pipeline_data, dict) and 'nodes' in pipeline_data):
            current_app.logger.warning(f"Pipeline {pipeline.id} has an unrecognized definition format.")
            return jsonify({'status': 'success', 'message': 'Pipeline triggered but had no valid nodes to execute.'}), 202

        # --- Fetch API keys and webhook URL once at the start ---
        chatgpt_setting = Setting.query.filter_by(key='chatgpt_api_key').first()
        discord_setting = Setting.query.filter_by(key='discord_webhook').first()
        chatgpt_api_key = chatgpt_setting.value if chatgpt_setting else None
        discord_webhook_url = discord_setting.value if discord_setting else None

        # Iterate through all nodes defined in the pipeline
        for node in pipeline_data.get('nodes', {}).values():
            if not isinstance(node, dict):
                continue
            
            node_name = node.get('name')
            node_type = node.get('type')

            # --- Step 1: Execute Script Node ---
            if node_type == 'script' and node.get('content'):
                script_name = node.get('name', 'Untitled Script')
                script_content = node.get('content')
                current_app.logger.info(f"Executing script node: '{script_name}'")
                output, error = execute_ssh_command(host, script_content)
                pipeline_context["script_outputs"].append(f"--- Output of '{script_name}' ---\n{output}")
                if error:
                    pipeline_context["errors"].append(f"--- Error from '{script_name}' ---\n{error}")
                    break # Stop pipeline on error

            # --- Step 2: AI Analysis Node ---
            elif node_name == 'AI Analysis':
                current_app.logger.info("Executing action node: 'AI Analysis'")
                full_diagnostic_data = "\n".join(pipeline_context["script_outputs"])
                prompt_context = f"A Zabbix alert named '{trigger_name}' occurred on host '{host.name}'. The following diagnostic data was collected."
                ai_result = get_ai_analysis(full_diagnostic_data, prompt_context, api_key=chatgpt_api_key)
                pipeline_context["ai_analysis"] = ai_result

            # --- Step 3: Notify Discord Node ---
            elif node_name == 'Notify Discord':
                current_app.logger.info("Executing action node: 'Notify Discord'")
                
                # Construct the full, untruncated message
                message = (
                    f"**Zabbix Alert Triage Report**\n"
                    f"**Host:** `{host.name}`\n"
                    f"**Trigger:** `{trigger_name}`\n"
                    f"**Pipeline:** `{pipeline.name}`\n"
                    f"----------------------------------------\n"
                    f"**AI Synopsis & Recommendations:**\n"
                    f"```\n{pipeline_context.get('ai_analysis', 'N/A')}\n```\n"
                    f"----------------------------------------\n"
                    f"**Raw Diagnostic Output:**\n"
                    f"```\n{''.join(pipeline_context.get('script_outputs', ['No output.']))}\n```"
                )
                
                # Pass the full message to the smart send_to_discord function
                send_to_discord(discord_webhook_url, message)

    except json.JSONDecodeError:
        current_app.logger.error(f"Could not execute pipeline {pipeline.id}: Invalid JSON in definition.")
        return jsonify({'error': 'Pipeline definition is not valid JSON.'}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during pipeline execution: {e}")
        return jsonify({'error': 'An unexpected error occurred during pipeline execution.'}), 500

    return jsonify({'status': 'success', 'message': 'Pipeline executed successfully.'}), 202
