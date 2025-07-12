from github import Github, UnknownObjectException

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
