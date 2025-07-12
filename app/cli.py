import click
from app import db
from app.models import User, Group
from werkzeug.security import generate_password_hash

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
            # 1. Ensure Admin group exists
            admin_group = Group.query.filter_by(name='Admin').first()
            if not admin_group:
                click.echo("Admin group not found, creating it...")
                admin_group = Group(name='Admin')
                # Define default full permissions for Admin
                admin_group.set_permissions({
                    "hosts": "full", 
                    "scripts": "full", 
                    "pipelines": "full", 
                    "users": "full", 
                    "settings": "full",
                    "groups": "full" # Added permissions for group management
                })
                db.session.add(admin_group)
                db.session.commit()
                click.echo(f"Admin group '{admin_group.name}' created with ID: {admin_group.id}")
            else:
                click.echo(f"Admin group '{admin_group.name}' already exists with ID: {admin_group.id}")

            # 2. Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                click.echo(f"User '{username}' already exists. Updating password and assigning to Admin group...")
                existing_user.set_password(password)
                existing_user.group = admin_group # Assign to Admin group
                db.session.commit()
                click.echo(f"Password for user '{username}' updated and assigned to '{admin_group.name}' group.")
            else:
                # 3. Create the new Admin user
                click.echo(f"Creating new Admin user '{username}'...")
                new_user = User(username=username, email=f"{username}@fysseree.local", group=admin_group)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                click.echo(f"Admin user '{username}' created successfully and assigned to '{admin_group.name}' group.")

            click.echo("Initial Admin setup complete.")

    # You can add other user management commands here later, e.g.,
    # @user.command('list')
    # def list_users():
    #     """Lists all users."""
    #     with app.app_context():
    #         users = User.query.all()
    #         for user in users:
    #             click.echo(f"ID: {user.id}, Username: {user.username}, Group: {user.group.name if user.group else 'None'}")

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
                    "hosts": "full", 
                    "scripts": "full", 
                    "pipelines": "full", 
                    "users": "none", 
                    "settings": "none",
                    "groups": "none"
                },
                'Viewer': {
                    "hosts": "view", 
                    "scripts": "view", 
                    "pipelines": "view", 
                    "users": "none", 
                    "settings": "none",
                    "groups": "none"
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

