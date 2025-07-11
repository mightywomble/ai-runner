from flask import render_template, request, redirect, url_for, flash, jsonify
from . import bp
from app import db
from app.models import Host
import paramiko

# A list of common distros for the dropdown.
# In a more advanced setup, this could come from the database.
distros = ['Ubuntu', 'Debian', 'Arch', 'CentOS', 'Fedora', 'Other']

@bp.route('/', methods=['GET', 'POST'])
def hosts():
    if request.method == 'POST':
        if not all(k in request.form for k in ['name', 'ip_address', 'os_type', 'ssh_user']):
            flash('All fields are required.', 'error')
            return redirect(url_for('hosts.hosts'))
        
        new_host = Host(
            name=request.form['name'],
            ip_address=request.form['ip_address'],
            os_type=request.form['os_type'],
            ssh_user=request.form['ssh_user'],
            location=request.form.get('location'),
            description=request.form.get('description'),
            # Only save distro if OS is Linux
            distro=request.form.get('distro') if request.form['os_type'] == 'Linux' else None
        )
        db.session.add(new_host)
        try:
            db.session.commit()
            flash(f'Host "{new_host.name}" added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding host: {e}', 'error')

        return redirect(url_for('hosts.hosts'))

    all_hosts = Host.query.all()
    return render_template('hosts/hosts.html', title='Manage Hosts', hosts=all_hosts, distros=distros)

@bp.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.get_json()
    ip_address = data.get('ip_address')
    ssh_user = data.get('ssh_user')

    if not ip_address or not ssh_user:
        return jsonify({'success': False, 'error': 'Missing IP address or username.'}), 400

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip_address, username=ssh_user, password=None, look_for_keys=True, timeout=5)
        client.close()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/delete/<int:host_id>', methods=['POST'])
def delete_host(host_id):
    host_to_delete = Host.query.get_or_404(host_id)
    try:
        db.session.delete(host_to_delete)
        db.session.commit()
        flash(f'Host "{host_to_delete.name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting host: {e}', 'error')
    return redirect(url_for('hosts.hosts'))

@bp.route('/edit/<int:host_id>', methods=['GET', 'POST'])
def edit_host(host_id):
    host_to_edit = Host.query.get_or_404(host_id)
    if request.method == 'POST':
        host_to_edit.name = request.form['name']
        host_to_edit.ip_address = request.form['ip_address']
        host_to_edit.os_type = request.form['os_type']
        host_to_edit.ssh_user = request.form['ssh_user']
        host_to_edit.location = request.form.get('location')
        host_to_edit.description = request.form.get('description')
        host_to_edit.distro = request.form.get('distro') if request.form['os_type'] == 'Linux' else None
        
        try:
            db.session.commit()
            flash(f'Host "{host_to_edit.name}" has been updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating host: {e}', 'error')
        return redirect(url_for('hosts.hosts'))
    
    return render_template('hosts/edit_host.html', title=f'Edit {host_to_edit.name}', host=host_to_edit, distros=distros)
