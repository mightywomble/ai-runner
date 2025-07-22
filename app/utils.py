# Combined imports for all utility functions
import os
import subprocess
import socket
import base64
import paramiko
import requests # Import requests for Discord notifications
from openai import OpenAI
from github import Github, UnknownObjectException
from flask import current_app
import time # Import time for rate limiting

# --- GitHub Functions ---
def push_to_github(repo_name, token, file_path, content, commit_message):
    """
    Pushes a file to a specified GitHub repository.
    Creates the file if it doesn't exist, or updates it if it does.
    """
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        try:
            existing_file = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing_file.sha
            )
            return f"Successfully updated '{file_path}' in '{repo_name}'."
        except UnknownObjectException:
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content
            )
            return f"Successfully created '{file_path}' in '{repo_name}'."
    except Exception as e:
        raise Exception(f"GitHub API Error: {e}")

def get_repo_scripts_recursive(repo, path=""):
    """Recursively fetches all script files from a GitHub repository."""
    scripts = []
    try:
        contents = repo.get_contents(path)
        for content_file in contents:
            if content_file.type == 'dir':
                scripts.extend(get_repo_scripts_recursive(repo, content_file.path))
            else:
                scripts.append({
                    'name': content_file.name,
                    'path': content_file.path,
                    'icon': get_script_icon(content_file.name)
                })
    except Exception as e:
        print(f"Could not get contents of {path}: {e}")
    return scripts

# --- Helper Functions ---
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

def get_distros():
    """Return a list of supported Linux distributions."""
    return [
        'Ubuntu', 'Debian', 'CentOS', 'RHEL', 'Fedora', 'SUSE', 'OpenSUSE',
        'Alpine', 'Arch', 'Manjaro', 'Mint', 'Pop!_OS', 'Kali',
        'Rocky Linux', 'AlmaLinux', 'Amazon Linux', 'Other'
    ]

# --- SSH, AI, and Notification Functions ---
def execute_ssh_command(host, command):
    """
    Executes a command on a remote host via SSH using Paramiko and returns the output.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_to = host.ip_address if host.ip_address else host.name
        current_app.logger.info(f"Attempting SSH connection to {connect_to} for user {host.ssh_user}")

        if hasattr(host, 'ssh_key') and host.ssh_key:
            current_app.logger.info("Connecting using explicit SSH key from database.")
            key_path = os.path.expanduser(host.ssh_key)
            client.connect(connect_to, username=host.ssh_user, key_filename=key_path, port=22, timeout=10)
        elif hasattr(host, 'password') and host.password:
            current_app.logger.info("Connecting using explicit password from database.")
            client.connect(connect_to, username=host.ssh_user, password=host.password, port=22, timeout=10)
        else:
            current_app.logger.info("No explicit credentials in DB. Attempting connection with default agent keys.")
            client.connect(connect_to, username=host.ssh_user, port=22, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        client.close()
        current_app.logger.info("SSH command executed successfully.")
        return output, error
    except Exception as e:
        current_app.logger.error(f"Exception during SSH command execution: {e}")
        return None, str(e)

def get_ai_analysis(diagnostic_data, context, api_key):
    """
    Sends diagnostic data to OpenAI for analysis and returns the response.
    """
    try:
        if not api_key:
            current_app.logger.error("AI analysis call failed: No API key was provided.")
            return "Error: AI analysis is not configured because the OpenAI API key is missing."

        client = OpenAI(api_key=api_key)
        prompt = f"""
        You are an expert systems administrator and IT operations analyst.
        {context}

        Here is the diagnostic data collected from the server:
        ---
        {diagnostic_data}
        ---

        Based on the data, please provide:
        1. A brief, clear synopsis of the likely problem.
        2. A list of recommended, actionable troubleshooting steps to resolve the issue.
        3. Any other important observations or potential underlying causes.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert systems administrator and IT operations analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        current_app.logger.error(f"Error during AI analysis: {e}")
        return f"An error occurred while trying to get AI analysis: {e}"

def send_to_discord(webhook_url, message_content):
    """
    Sends a message to a Discord webhook, splitting it into multiple messages if it's too long.
    """
    if not webhook_url:
        current_app.logger.error("Discord notification failed: Webhook URL is not configured.")
        return False, "Discord webhook URL not provided."

    max_length = 1990  # Safe character limit for Discord messages
    
    def post_chunk(chunk):
        """Helper function to post a single chunk to Discord."""
        data = {"content": chunk}
        try:
            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            return True, response.status_code
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Failed to send chunk to Discord: {e}")
            return False, str(e)

    if len(message_content) <= max_length:
        # If the message is short enough, send it in one go.
        success, status = post_chunk(message_content)
        if success:
            current_app.logger.info("Successfully sent single-part message to Discord.")
            return True, "Message sent to Discord."
        else:
            return False, status
    else:
        # If the message is too long, split it into chunks.
        current_app.logger.info(f"Message is too long ({len(message_content)} chars). Splitting into multiple parts.")
        chunks = []
        remaining_text = message_content
        while len(remaining_text) > 0:
            if len(remaining_text) <= max_length:
                chunks.append(remaining_text)
                break
            
            # Find the last newline before the max_length to avoid breaking mid-line
            split_point = remaining_text.rfind('\n', 0, max_length)
            if split_point == -1: # If no newline, just split at the max length
                split_point = max_length
            
            chunks.append(remaining_text[:split_point])
            remaining_text = remaining_text[split_point:].lstrip()

        # Send each chunk as a separate message
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk_header = f"**(Message {i+1}/{total_chunks})**\n"
            success, status = post_chunk(chunk_header + chunk)
            if not success:
                return False, f"Failed to send chunk {i+1}: {status}"
            time.sleep(1) # Add a small delay to avoid rate limiting

        current_app.logger.info(f"Successfully sent {total_chunks}-part message to Discord.")
        return True, "Multi-part message sent to Discord."


# --- Validation and Testing Functions ---
def test_ssh_connection(ip_address, ssh_user):
    """Test SSH connection to a host using the system's SSH command."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip_address, 22))
        sock.close()
        
        if result != 0:
            return False, f"Cannot reach {ip_address} on port 22"
        
        cmd = [
            'ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no', f'{ssh_user}@{ip_address}',
            'echo "SSH connection successful"'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return True, "SSH connection successful"
        else:
            return False, f"SSH connection failed: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return False, "SSH connection timed out"
    except Exception as e:
        return False, f"Error testing SSH connection: {str(e)}"

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
