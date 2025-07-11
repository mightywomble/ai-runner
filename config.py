import os
import yaml

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def get_app_config():
        try:
            with open('config.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_app_config(data):
        with open('config.yaml', 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
