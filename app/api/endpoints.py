from flask import jsonify, request, abort
from functools import wraps
from . import bp
from app.models import User, Host, Script, Pipeline
from app import db

def require_api_key(f):
    """Decorator to protect routes with API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            abort(401, description="API key is missing.")
        
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            abort(401, description="Invalid API key.")
        
        # You could attach the user to the request context if needed
        # from flask import g
        # g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/v1/hosts', methods=['GET'])
@require_api_key
def get_hosts():
    """API endpoint to list all hosts."""
    hosts = Host.query.all()
    return jsonify([{'id': h.id, 'name': h.name, 'ip_address': h.ip_address} for h in hosts])

@bp.route('/v1/hosts', methods=['POST'])
@require_api_key
def create_host():
    """API endpoint to create a new host."""
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'ip_address', 'ssh_user', 'os_type']):
        abort(400, description="Missing required host data.")
    
    new_host = Host(**data)
    db.session.add(new_host)
    db.session.commit()
    return jsonify({'message': 'Host created successfully', 'id': new_host.id}), 201

# --- Placeholder Endpoints ---
# The following endpoints are defined to match the OpenAPI spec but need full implementation.

@bp.route('/v1/hosts/<int:host_id>', methods=['PUT'])
@require_api_key
def update_host(host_id):
    return jsonify({"status": "success", "message": f"Host {host_id} updated (placeholder)."}), 200

@bp.route('/v1/scripts/local', methods=['GET'])
@require_api_key
def get_local_scripts():
    scripts = Script.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'type': s.script_type} for s in scripts])

@bp.route('/v1/scripts/github', methods=['GET'])
@require_api_key
def get_github_scripts():
    # This would require logic to fetch from GitHub
    return jsonify({"message": "GitHub scripts endpoint (placeholder)."}), 200

@bp.route('/v1/scripts/run', methods=['POST'])
@require_api_key
def run_script():
    data = request.get_json()
    return jsonify({"status": "success", "message": f"Running script (placeholder).", "details": data}), 200

@bp.route('/v1/pipelines/local', methods=['GET'])
@require_api_key
def get_local_pipelines():
    pipelines = Pipeline.query.all()
    return jsonify([{'id': p.id, 'name': p.name} for p in pipelines])

@bp.route('/v1/pipelines/run', methods=['POST'])
@require_api_key
def run_pipeline():
    data = request.get_json()
    return jsonify({"status": "success", "message": f"Running pipeline (placeholder).", "details": data}), 200

@bp.route('/v1/backup/create', methods=['POST'])
@require_api_key
def create_backup_api():
    # This would trigger the backup creation logic
    return jsonify({"status": "success", "message": "Backup creation initiated (placeholder)."}), 200

@bp.route('/v1/backup/restore', methods=['POST'])
@require_api_key
def restore_backup_api():
    # This would handle the file upload and restore logic
    return jsonify({"status": "success", "message": "Restore process initiated (placeholder)."}), 200
