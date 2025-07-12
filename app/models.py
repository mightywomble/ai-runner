from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json # Import json to handle permissions column

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Permissions stored as a JSON string
    # Example: {"hosts": "full", "scripts": "view", "pipelines": "full", "users": "none", "settings": "none"}
    permissions = db.Column(db.Text, nullable=False, default='{}') 
    users = db.relationship('User', backref='group', lazy=True) # Relationship to users

    def __repr__(self):
        return f"Group('{self.name}')"

    def get_permissions(self):
        """Returns the permissions dictionary."""
        return json.loads(self.permissions) if self.permissions else {}

    def set_permissions(self, perms_dict):
        """Sets the permissions from a dictionary."""
        self.permissions = json.dumps(perms_dict)

    def has_permission(self, feature, access_level):
        """
        Checks if the group has a specific access level for a feature.
        Access levels: 'none', 'view', 'full'
        """
        current_perms = self.get_permissions()
        feature_access = current_perms.get(feature, 'none')

        if access_level == 'none':
            return feature_access == 'none'
        elif access_level == 'view':
            return feature_access in ['view', 'full']
        elif access_level == 'full':
            return feature_access == 'full'
        return False


class User(db.Model, UserMixin): # Inherit UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True) # Link to Group

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_group_permissions(self):
        """Returns the permissions of the user's associated group."""
        if self.group:
            return self.group.get_permissions()
        return {}

    def can(self, feature, access_level):
        """Checks if the user has a specific access level for a feature via their group."""
        if self.group:
            return self.group.has_permission(feature, access_level)
        return False # No group, no permissions


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(100), nullable=False)
    os_type = db.Column(db.String(50), nullable=False)
    distro = db.Column(db.String(50))
    ssh_user = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)

    def __repr__(self):
        return f"Host('{self.name}', '{self.ip_address}')"

class Script(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    script_type = db.Column(db.String(64), default='Bash Script')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Script {self.name}>'

class Pipeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    definition = db.Column(db.Text) # Storing the pipeline definition as YAML or JSON

    def __repr__(self):
        return f"Pipeline('{self.name}')"
