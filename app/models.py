from app import db

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True, nullable=False)
    ip_address = db.Column(db.String(64), index=True, unique=True, nullable=False)
    os_type = db.Column(db.String(32), nullable=False)
    ssh_user = db.Column(db.String(64), nullable=False)
    location = db.Column(db.String(128), nullable=True)
    distro = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Host {self.name}>'

class Script(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    script_type = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f'<Script {self.name}>'
