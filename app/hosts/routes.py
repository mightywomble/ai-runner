from flask import render_template, request, redirect, url_for, flash, jsonify
from . import bp  # Correct: Imports the 'bp' object from the __init__.py in the same folder
from .. import db
from ..models import Host, Group
# The problematic imports have been removed from here

@bp.route('/hosts', methods=['GET', 'POST'])
def hosts_page():
    from ..utils import get_distros  # Import is now inside the function
    if request.method == 'POST':
        # This handles adding a new host
        name = request.form.get('name')
        ip_address = request.form.get('ip_address')
        os_type = request.form.get('os_type')
        distro = request.form.get('distro') if os_type == 'Linux' else None
        ssh_user = request.form.get('ssh_user')
        location = request.form.get('location')
        description = request.form.get('description')
        group_id = request.form.get('group_id')

        new_host = Host(
            name=name,
            ip_address=ip_address,
            os_type=os_type,
            distro=distro,
            ssh_user=ssh_user,
            location=location,
            description=description,
            group_id=group_id if group_id else None
        )
        db.session.add(new_host)
        db.session.commit()
        flash('Host added successfully!', 'success')
        return redirect(url_for('hosts.hosts_page'))

    groups = Group.query.all()
    # Create a dictionary to hold hosts grouped by their group_id
    hosts_by_group = {group.id: [] for group in groups}
    # Get all hosts that have a group
    grouped_hosts = Host.query.filter(Host.group_id.isnot(None)).all()
    for host in grouped_hosts:
        if host.group_id in hosts_by_group:
            hosts_by_group[host.group_id].append(host)

    # Get hosts that are not in any group
    ungrouped_hosts = Host.query.filter(Host.group_id.is_(None)).all()

    return render_template(
        'hosts/hosts.html',
        distros=get_distros(),
        groups=groups,
        hosts_by_group=hosts_by_group,
        ungrouped_hosts=ungrouped_hosts
    )

@bp.route('/hosts/groups', methods=['POST'])
def add_group():
    name = request.form.get('group_name')
    if name:
        # Check if group already exists
        if Group.query.filter_by(name=name).first():
            flash(f'Group "{name}" already exists.', 'error')
        else:
            new_group = Group(name=name)
            db.session.add(new_group)
            db.session.commit()
            flash(f'Group "{name}" added successfully!', 'success')
    return redirect(url_for('hosts.hosts_page'))

@bp.route('/hosts/groups/<int:group_id>/delete', methods=['POST'])
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    # Note: You might want to decide what happens to hosts in a deleted group.
    # Here, we'll set their group_id to None, making them "ungrouped".
    for host in group.hosts:
        host.group_id = None
    db.session.delete(group)
    db.session.commit()
    flash(f'Group "{group.name}" deleted successfully!', 'success')
    return redirect(url_for('hosts.hosts_page'))

@bp.route('/hosts/<int:host_id>/edit', methods=['GET', 'POST'])
def edit_host(host_id):
    from ..utils import get_distros  # Import is now inside the function
    host = Host.query.get_or_404(host_id)
    if request.method == 'POST':
        host.name = request.form.get('name')
        host.ip_address = request.form.get('ip_address')
        host.os_type = request.form.get('os_type')
        host.distro = request.form.get('distro') if host.os_type == 'Linux' else None
        host.ssh_user = request.form.get('ssh_user')
        host.location = request.form.get('location')
        host.description = request.form.get('description')
        host.group_id = request.form.get('group_id')
        db.session.commit()
        flash('Host updated successfully!', 'success')
        return redirect(url_for('hosts.hosts_page'))

    groups = Group.query.all()
    return render_template('hosts/edit_host.html', host=host, distros=get_distros(), groups=groups)

@bp.route('/hosts/<int:host_id>/delete', methods=['POST'])
def delete_host(host_id):
    host = Host.query.get_or_404(host_id)
    db.session.delete(host)
    db.session.commit()
    flash('Host deleted successfully!', 'success')
    return redirect(url_for('hosts.hosts_page'))

@bp.route('/hosts/test_connection', methods=['POST'])
def test_connection():
    try:
        from ..utils import test_ssh_connection
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        ip_address = data.get('ip_address')
        ssh_user = data.get('ssh_user')
        
        if not ip_address or not ssh_user:
            return jsonify({'success': False, 'message': 'IP address and SSH user are required'}), 400
        
        success, message = test_ssh_connection(ip_address, ssh_user)
        return jsonify({'success': success, 'message': message})
        
    except ImportError:
        return jsonify({'success': False, 'message': 'SSH testing function not available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
