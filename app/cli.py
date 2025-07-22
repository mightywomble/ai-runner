import click
import getpass
from app import db
from app.models import User, Group

def register_cli_commands(app):
    """Register custom CLI commands with the Flask app."""

    @app.cli.group()
    def user():
        """User management commands."""
        pass

    @user.command('create-admin')
    @click.argument('username')
    @click.password_option()
    def create_admin(username, password):
        """Creates an initial Admin user and group."""
        with app.app_context():
            admin_group = Group.query.filter_by(name='Admin').first()
            if not admin_group:
                click.echo("Admin group not found, creating it...")
                admin_group = Group(name='Admin')
                admin_group.set_permissions({
                    "hosts": "full", "scripts": "full", "pipelines": "full", 
                    "users": "full", "settings": "full", "groups": "full"
                })
                db.session.add(admin_group)
                db.session.commit()
                click.echo(f"Admin group '{admin_group.name}' created.")
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                click.echo(f"User '{username}' already exists. Updating password and assigning to Admin group...")
                existing_user.set_password(password)
                existing_user.group = admin_group
                db.session.commit()
                click.echo(f"Password for user '{username}' updated and assigned to '{admin_group.name}' group.")
            else:
                click.echo(f"Creating new Admin user '{username}'...")
                # Also generate an API key for the admin user
                new_user = User(username=username, email=f"{username}@fysseree.local", group=admin_group)
                new_user.set_password(password)
                new_user.generate_api_key() 
                db.session.add(new_user)
                db.session.commit()
                click.echo(f"Admin user '{username}' created successfully and assigned to '{admin_group.name}' group.")

    @user.command('create-user')
    @click.argument('username')
    def create_user(username):
        """Creates a regular user with an API key."""
        if User.query.filter_by(username=username).first():
            click.echo(f'Error: User {username} already exists.')
            return
        password = getpass.getpass('Enter password: ')
        confirm_password = getpass.getpass('Confirm password: ')
        if password != confirm_password:
            click.echo('Error: Passwords do not match.')
            return
        new_user = User(username=username, email=f"{username}@fysseree.local")
        new_user.set_password(password)
        new_user.generate_api_key() # Crucially, generate the API key
        db.session.add(new_user)
        db.session.commit()
        click.echo(f'User {username} created successfully.')

    @user.command('list-users')
    def list_users():
        """Lists all users and their API keys."""
        users = User.query.all()
        if not users:
            click.echo("No users found.")
            return
        click.echo("{:<20} {:<45}".format("Username", "API Key"))
        click.echo("-" * 65)
        for user in users:
            click.echo("{:<20} {:<45}".format(user.username, user.api_key or "N/A"))

    @user.command('show-key')
    @click.argument('username')
    def show_key(username):
        """Shows the API key for a specific user."""
        user = User.query.filter_by(username=username).first()
        if user:
            if user.api_key:
                click.echo(f"API Key for {username}: {user.api_key}")
            else:
                click.echo(f"User {username} does not have an API key.")
        else:
            click.echo(f"User {username} not found.")

    @app.cli.group()
    def group():
        """Group management commands."""
        pass

    @group.command('create-default-groups')
    def create_default_groups():
        """Creates default Engineer and Viewer groups if they don't exist."""
        with app.app_context():
            default_groups_data = {
                'Engineer': {
                    "hosts": "full", "scripts": "full", "pipelines": "full", 
                    "users": "none", "settings": "none", "groups": "none"
                },
                'Viewer': {
                    "hosts": "view", "scripts": "view", "pipelines": "view", 
                    "users": "none", "settings": "none", "groups": "none"
                }
            }

            for group_name, perms in default_groups_data.items():
                existing_group = Group.query.filter_by(name=group_name).first()
                if not existing_group:
                    new_group = Group(name=group_name)
                    new_group.set_permissions(perms)
                    db.session.add(new_group)
                    click.echo(f"Group '{group_name}' created.")
                else:
                    click.echo(f"Group '{group_name}' already exists.")
            db.session.commit()
            click.echo("Default groups setup complete.")
