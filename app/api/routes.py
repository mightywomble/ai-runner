from flask import render_template, jsonify
from flask_login import login_required
from . import bp
from app.models import User

@bp.route('/docs')
@login_required
def docs():
    """Renders the interactive API documentation page."""
    # Fetch all users who have an API key to populate the dropdown
    users_with_keys = User.query.filter(User.api_key.isnot(None)).all()
    return render_template('api/docs.html', title="API Documentation", users_with_keys=users_with_keys)

@bp.route('/v1/openapi.json')
def openapi_spec():
    """Serves the OpenAPI 3.0 specification file."""
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Fysseree AIOps REST API",
            "description": "A comprehensive REST API for managing all resources within the Fysseree AIOps platform, including hosts, scripts, pipelines, and administrative tasks.",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "/api/v1",
                "description": "API Version 1"
            }
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [
            {
                "ApiKeyAuth": []
            }
        ],
        "paths": {
            "/hosts": {
                "get": {
                    "summary": "List All Hosts",
                    "description": "Retrieves a list of all configured hosts.",
                    "tags": ["Hosts"],
                    "responses": {
                        "200": {"description": "A list of hosts."}
                    }
                },
                "post": {
                    "summary": "Add a New Host",
                    "description": "Creates a new host in the system.",
                    "tags": ["Hosts"],
                    "requestBody": {
                        "required": True,
                        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Host" } } }
                    },
                    "responses": {
                        "201": {"description": "Host created successfully."}
                    }
                }
            },
            "/hosts/{host_id}": {
                "put": {
                    "summary": "Update a Host",
                    "description": "Updates the details of a specific host.",
                    "tags": ["Hosts"],
                    "parameters": [{"name": "host_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "requestBody": {
                        "required": True,
                        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Host" } } }
                    },
                    "responses": {
                        "200": {"description": "Host updated successfully."}
                    }
                }
            },
            "/scripts/local": {
                "get": {
                    "summary": "List Local Scripts",
                    "description": "Retrieves a list of all scripts saved locally in the application.",
                    "tags": ["Scripts"],
                    "responses": {
                        "200": {"description": "A list of local scripts."}
                    }
                }
            },
            "/scripts/github": {
                "get": {
                    "summary": "List GitHub Scripts",
                    "description": "Retrieves a list of scripts from the configured GitHub repository.",
                    "tags": ["Scripts"],
                    "responses": {
                        "200": {"description": "A list of scripts from GitHub."}
                    }
                }
            },
            "/scripts/run": {
                "post": {
                    "summary": "Run a Script",
                    "description": "Executes a local or GitHub script on a specified host.",
                    "tags": ["Scripts"],
                    "requestBody": {
                        "required": True,
                        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ScriptRun" } } }
                    },
                    "responses": {
                        "200": {"description": "Script execution result."}
                    }
                }
            },
            "/pipelines/local": {
                "get": {
                    "summary": "List Local Pipelines",
                    "description": "Retrieves a list of all pipelines saved locally.",
                    "tags": ["Pipelines"],
                    "responses": {
                        "200": {"description": "A list of local pipelines."}
                    }
                }
            },
            "/pipelines/run": {
                "post": {
                    "summary": "Run a Pipeline",
                    "description": "Executes a specified local pipeline.",
                    "tags": ["Pipelines"],
                    "requestBody": {
                        "required": True,
                        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/PipelineRun" } } }
                    },
                    "responses": {
                        "200": {"description": "Pipeline execution result."}
                    }
                }
            },
            "/backup/create": {
                "post": {
                    "summary": "Create a Backup",
                    "description": "Triggers the creation of a new system backup.",
                    "tags": ["Admin"],
                    "responses": {
                        "200": {"description": "Backup created successfully. Returns filename."}
                    }
                }
            },
            "/backup/restore": {
                "post": {
                    "summary": "Restore from Backup",
                    "description": "Restores the system from an uploaded backup file.",
                    "tags": ["Admin"],
                    "requestBody": {
                        "required": True,
                        "content": { "multipart/form-data": { "schema": { "type": "object", "properties": { "file": { "type": "string", "format": "binary" } } } } }
                    },
                    "responses": {
                        "200": {"description": "Restore process initiated."}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Host": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ip_address": {"type": "string"},
                        "ssh_user": {"type": "string"},
                        "os_type": {"type": "string"},
                        "distro": {"type": "string"},
                        "location": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "ScriptRun": {
                    "type": "object",
                    "properties": {
                        "script_id": {"type": "integer"},
                        "host_id": {"type": "integer"},
                        "source": {"type": "string", "enum": ["local", "github"]},
                        "github_path": {"type": "string"}
                    }
                },
                "PipelineRun": {
                    "type": "object",
                    "properties": {
                        "pipeline_id": {"type": "integer"}
                    }
                }
            }
        }
    }
    return jsonify(spec)
