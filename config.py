import os
import yaml

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth Settings - These will be loaded from config.yaml
    # They are set as class attributes for direct access during app creation
    GOOGLE_CLIENT_ID = None
    GOOGLE_CLIENT_SECRET = None

    @staticmethod
    def get_app_config():
        """
        Loads application-wide settings from config.yaml.
        """
        try:
            with open('config.yaml', 'r') as f:
                app_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            app_config = {}
        except yaml.YAMLError as e:
            print(f"Error loading config.yaml: {e}")
            app_config = {} # Return empty dict on error

        # Populate Config class attributes for Authlib initialization
        Config.GOOGLE_CLIENT_ID = app_config.get('google_client_id')
        Config.GOOGLE_CLIENT_SECRET = app_config.get('google_client_secret')

        return app_config

    @staticmethod
    def save_app_config(data):
        """
        Saves application-wide settings to config.yaml.
        """
        with open('config.yaml', 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

# Call get_app_config once to load initial settings, especially for OAuth client IDs
# This ensures GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are populated before app creation
Config.get_app_config()
