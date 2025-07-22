import os
import json
import tarfile
import shutil
from datetime import datetime
from flask import render_template, current_app, request, flash, redirect, url_for, send_from_directory
from flask_login import login_required
from werkzeug.utils import secure_filename
from . import bp
from app.models import Host, Script, Pipeline, Setting
from app import db
from app.utils import push_to_github

@bp.route('/')
@login_required
def backup():
    """
    Renders the main backup and restore page.
    """
    return render_template('backup/backup.html', title="Backup and Restore")

@bp.route('/create', methods=['POST'])
@login_required
def create_backup():
    """
    Creates a backup of hosts, scripts, pipelines, and settings.
    """
    try:
        backup_dir = os.path.join(current_app.instance_path, 'backup_temp')
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir)

        # Backup data
        hosts = Host.query.all()
        hosts_data = [{'id': h.id, 'name': h.name, 'ip_address': h.ip_address, 'ssh_user': h.ssh_user, 'os_type': h.os_type, 'distro': h.distro, 'location': h.location, 'description': h.description} for h in hosts]
        with open(os.path.join(backup_dir, 'hosts.json'), 'w') as f:
            json.dump(hosts_data, f, indent=4)

        scripts = Script.query.all()
        scripts_data = [{'id': s.id, 'name': s.name, 'script_type': s.script_type, 'content': s.content} for s in scripts]
        with open(os.path.join(backup_dir, 'scripts.json'), 'w') as f:
            json.dump(scripts_data, f, indent=4)

        pipelines = Pipeline.query.all()
        pipelines_data = [{'id': p.id, 'name': p.name, 'description': p.description, 'definition': p.definition} for p in pipelines]
        with open(os.path.join(backup_dir, 'pipelines.json'), 'w') as f:
            json.dump(pipelines_data, f, indent=4)
        
        settings = Setting.query.all()
        settings_data = [{'id': s.id, 'key': s.key, 'value': s.value} for s in settings]
        with open(os.path.join(backup_dir, 'settings.json'), 'w') as f:
            json.dump(settings_data, f, indent=4)


        # Create tar.gz file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.tar.gz'
        backup_path = os.path.join(current_app.instance_path, 'backups')
        os.makedirs(backup_path, exist_ok=True)
        
        archive_file = os.path.join(backup_path, backup_filename)
        with tarfile.open(archive_file, 'w:gz') as tar:
            tar.add(backup_dir, arcname='backup_content')

        shutil.rmtree(backup_dir)
        flash(f'Backup created successfully: {backup_filename}', 'success')
        return render_template('backup/backup.html', title="Backup and Restore", backup_filename=backup_filename)

    except Exception as e:
        flash(f'Error creating backup: {e}', 'danger')
        return redirect(url_for('backup.backup'))

@bp.route('/download/<filename>')
@login_required
def download_backup(filename):
    backup_path = os.path.join(current_app.instance_path, 'backups')
    return send_from_directory(directory=backup_path, path=filename, as_attachment=True)

@bp.route('/push_to_github', methods=['POST'])
@login_required
def push_backup_to_github_route():
    backup_filename = request.form.get('backup_filename')
    if not backup_filename:
        flash('No backup file specified.', 'danger')
        return redirect(url_for('backup.backup'))

    backup_filepath = os.path.join(current_app.instance_path, 'backups', backup_filename)
    if not os.path.exists(backup_filepath):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('backup.backup'))

    github_repo_setting = Setting.query.filter_by(key='github_repo').first()
    github_token_setting = Setting.query.filter_by(key='github_token').first()

    if not github_repo_setting or not github_token_setting or not github_repo_setting.value or not github_token_setting.value:
        flash('GitHub repository or token are not configured.', 'danger')
        return redirect(url_for('backup.backup'))

    repo_name = github_repo_setting.value
    token = github_token_setting.value
    
    try:
        with open(backup_filepath, 'rb') as f:
            content = f.read()
        
        response_message = push_to_github(repo_name, token, f'backups/{backup_filename}', content, f'feat: Add backup {backup_filename}')
        flash(f'Successfully pushed backup to GitHub: {response_message}', 'success')
    except Exception as e:
        flash(f'Failed to push backup to GitHub: {e}', 'danger')

    return redirect(url_for('backup.backup'))

@bp.route('/restore/preview', methods=['POST'])
@login_required
def preview_backup():
    if 'backup_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('backup.backup'))
    
    file = request.files['backup_file']
    if file.filename == '' or not file.filename.endswith('.tar.gz'):
        flash('No selected file or invalid file type. Please upload a .tar.gz file.', 'danger')
        return redirect(url_for('backup.backup'))

    filename = secure_filename(file.filename)
    upload_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    upload_dir = os.path.join(current_app.instance_path, 'uploads', upload_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    extract_dir = os.path.join(upload_dir, 'extracted')
    
    try:
        with tarfile.open(filepath, 'r:gz') as tar:
            tar.extractall(path=extract_dir)
        
        content_dir = os.path.join(extract_dir, 'backup_content')
        backup_summary = {}

        if os.path.exists(os.path.join(content_dir, 'hosts.json')):
            with open(os.path.join(content_dir, 'hosts.json'), 'r') as f:
                backup_summary['hosts'] = len(json.load(f))
        
        if os.path.exists(os.path.join(content_dir, 'scripts.json')):
            with open(os.path.join(content_dir, 'scripts.json'), 'r') as f:
                backup_summary['scripts'] = len(json.load(f))

        if os.path.exists(os.path.join(content_dir, 'pipelines.json')):
            with open(os.path.join(content_dir, 'pipelines.json'), 'r') as f:
                backup_summary['pipelines'] = len(json.load(f))

        if os.path.exists(os.path.join(content_dir, 'settings.json')):
            with open(os.path.join(content_dir, 'settings.json'), 'r') as f:
                backup_summary['settings'] = len(json.load(f))
        
        if not backup_summary:
            raise ValueError("The uploaded backup archive is empty or has an invalid structure.")

        return render_template('backup/restore_preview.html', title="Restore Preview", summary=backup_summary, upload_id=upload_id, filename=filename)

    except Exception as e:
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        flash(f'Error analyzing backup: {e}', 'danger')
        return redirect(url_for('backup.backup'))

@bp.route('/restore/execute', methods=['POST'])
@login_required
def execute_restore():
    upload_id = request.form.get('upload_id')
    restore_items = request.form.getlist('restore_items')

    if not upload_id or not restore_items:
        flash('Invalid restore request. Please start over.', 'danger')
        return redirect(url_for('backup.backup'))

    upload_dir = os.path.join(current_app.instance_path, 'uploads', upload_id)
    content_dir = os.path.join(upload_dir, 'extracted', 'backup_content')
    
    if not os.path.exists(content_dir):
        flash('Restore session expired or file not found. Please upload again.', 'danger')
        return redirect(url_for('backup.backup'))

    try:
        if 'hosts' in restore_items:
            db.session.query(Host).delete()
            with open(os.path.join(content_dir, 'hosts.json'), 'r') as f:
                for h_data in json.load(f):
                    h_data.pop('id', None); db.session.add(Host(**h_data))
        
        if 'scripts' in restore_items:
            db.session.query(Script).delete()
            with open(os.path.join(content_dir, 'scripts.json'), 'r') as f:
                for s_data in json.load(f):
                    s_data.pop('id', None); db.session.add(Script(**s_data))

        if 'pipelines' in restore_items:
            db.session.query(Pipeline).delete()
            with open(os.path.join(content_dir, 'pipelines.json'), 'r') as f:
                for p_data in json.load(f):
                    p_data.pop('id', None); db.session.add(Pipeline(**p_data))
        
        if 'settings' in restore_items:
            db.session.query(Setting).delete()
            with open(os.path.join(content_dir, 'settings.json'), 'r') as f:
                for s_data in json.load(f):
                    s_data.pop('id', None); db.session.add(Setting(**s_data))

        db.session.commit()
        flash(f'Successfully restored: {", ".join(restore_items)}', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during restore: {e}', 'danger')
    finally:
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)

    return redirect(url_for('backup.backup'))
