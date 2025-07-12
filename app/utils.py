from github import Github, UnknownObjectException
import subprocess
import socket

def get_script_icon(filename):
    """Returns a Font Awesome icon class based on the script's file extension."""
    if filename.endswith(('.sh', '.bash')):
        return 'fas fa-terminal'
    elif filename.endswith('.py'):
        return 'fab fa-python'
    elif filename.endswith(('.yml', '.yaml')):
        return 'fas fa-cogs'
    else:
        return 'fas fa-scroll'

def get_repo_scripts_recursive(repo, path=""):
    """Recursively fetches all script files from a GitHub repository."""
    scripts = []
    try:
        # Get all contents of the given path in the repository
        contents = repo.get_contents(path)
        for content_file in contents:
            if content_file.type == 'dir':
                # If it's a directory, recurse into it
                scripts.extend(get_repo_scripts_recursive(repo, content_file.path))
            else:
                # If it's a file, add it to our list
                scripts.append({
                    'name': content_file.name,
                    'path': content_file.path,
                    'icon': get_script_icon(content_file.name)
                })
    except Exception as e:
        # This can happen if a directory is empty or other API issues occur
        print(f"Could not get contents of {path}: {e}")
    return scripts

def get_distros():
    """Return a list of supported Linux distributions."""
    return [
        'Ubuntu',
        'Debian',
        'CentOS',
        'RHEL',
        'Fedora',
        'SUSE',
        'OpenSUSE',
        'Alpine',
        'Arch',
        'Manjaro',
        'Mint',
        'Pop!_OS',
        'Kali',
        'Rocky Linux',
        'AlmaLinux',
        'Amazon Linux',
        'Other'
    ]

def test_ssh_connection(ip_address, ssh_user):
    """Test SSH connection to a host."""
    try:
        # First test if the host is reachable on port 22
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip_address, 22))
        sock.close()
        
        if result != 0:
            return False, f"Cannot reach {ip_address} on port 22"
        
        # Test SSH connection with a simple command
        cmd = [
            'ssh',
            '-o', 'ConnectTimeout=10',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            f'{ssh_user}@{ip_address}',
            'echo "SSH connection successful"'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return True, "SSH connection successful"
        else:
            return False, f"SSH connection failed: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return False, "SSH connection timed out"
    except Exception as e:
        return False, f"Error testing SSH connection: {str(e)}"

# Add any other utility functions you might need
def validate_ip_address(ip):
    """Validate if the given string is a valid IP address."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_hostname(hostname):
    """Validate if the given string is a valid hostname."""
    import re
    if len(hostname) > 253:
        return False
    allowed = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$")
    return all(allowed.match(x) for x in hostname.split("."))
