
# AI-Runner: Your Intelligent DevOps Assistant

## Summary of App

AI-Runner is a web-based application designed to streamline DevOps operations by integrating AI-powered script generation, execution, and analysis with host management and pipeline automation. It provides a centralized platform for managing infrastructure tasks, automating workflows, and leveraging artificial intelligence to enhance efficiency and reduce manual effort.

## Meaning of App Name

The name "AI-Runner" signifies the core functionality of the application: it's a platform that **runs** various scripts and automated tasks, heavily leveraging **Artificial Intelligence** (AI) to assist in generating, analyzing, and executing these operations. It implies an intelligent agent that executes commands and workflows.

## Purpose of App

The primary purpose of AI-Runner is to empower DevOps engineers, system administrators, and developers with tools to:

-   **Generate scripts quickly:** Use natural language prompts to create Bash, Python, or Ansible scripts.
    
-   **Automate tasks:** Define and execute complex multi-step pipelines across multiple hosts.
    
-   **Manage infrastructure:** Centralize the management of remote hosts, including SSH credentials and operating system details.
    
-   **Analyze operations:** Get AI-driven insights into script dry runs and live execution outputs.
    
-   **Improve efficiency:** Reduce repetitive manual tasks and enhance the speed and reliability of deployments and system maintenance.
    
-   **Collaborate:** (Future potential) Provide a shared platform for teams to manage and execute operations.
    

## Feature List

-   **AI Script Generation:**
    
    -   Generate Bash commands, Bash scripts, Python scripts, and Ansible playbooks from natural language descriptions.
        
    -   Supports multiple AI providers (Gemini, ChatGPT).
        
-   **Script Management:**
    
    -   Save generated scripts locally within the application.
        
    -   Edit and delete saved scripts.
        
    -   Push local scripts to a GitHub repository (e.g., `dev` branch) organized by script type.
        
    -   Pull scripts from GitHub repositories.
        
-   **Host Management:**
    
    -   Add, edit, and delete remote hosts with details like IP address, SSH username, OS type, and group.
        
    -   Securely store host credentials (though for production, consider more robust secrets management).
        
-   **Script Execution:**
    
    -   Run generated or saved scripts on selected remote hosts.
        
    -   Option to run scripts with `sudo` privileges.
        
    -   View live execution output and errors.
        
-   **AI Analysis:**
    
    -   **Dry Run Analysis:** Get an AI-generated explanation of what a script will do before execution, including dependencies, expected outcomes, and potential issues.
        
    -   **Execution Output Analysis:** Analyze the output and errors from live script executions to aid in debugging and understanding.
        
-   **Pipeline Builder:**
    
    -   Visually construct multi-step pipelines by connecting hosts, scripts, and actions (like AI analysis, notifications).
        
    -   Save and load pipeline definitions.
        
    -   (Execution logic for pipelines is being developed/extended).
        
-   **Notifications:**
    
    -   Integrate with external services like Discord for execution notifications.
        
-   **Settings:**
    
    -   Configure AI API keys (Gemini, ChatGPT) and GitHub repository details.
        

## Install Instructions

To install and set up AI-Runner, follow these steps:

1.  **Clone the repository:**
    
    ```
    git clone <repository_url>
    cd ai_runner
    
    ```
    
2.  **Create a Python virtual environment (recommended):**
    
    ```
    python3 -m venv venv
    source venv/bin/activate
    
    ```
    
3.  **Install dependencies:**
    
    ```
    pip install -r requirements.txt
    
    ```
    
4.  **Set up Flask environment variables:**
    
    ```
    export FLASK_APP=run.py
    export FLASK_ENV=development # For development, use 'production' for deployment
    
    ```
    
    (You might want to add these to your `.bashrc` or `.zshrc` for persistence, or use a `.env` file with `python-dotenv`).
    
5.  **Initialize and migrate the database:** Since the database (`app.db`) is managed by Flask-Migrate, you need to set it up.
    
    ```
    flask db init
    flask db migrate -m "Initial database setup"
    flask db upgrade
    
    ```
    
    _If you previously had an `app.db` and deleted it, and are encountering errors with `flask db init`, you might need to delete the `migrations/` folder as well before running `flask db init`._
    

## Prerequisites Needed

Before running the application, ensure you have the following:

-   **Python 3.8+**: The application is built with Python.
    
-   **pip**: Python package installer.
    
-   **Git**: For cloning the repository.
    
-   **SSH Access to Remote Hosts**: To run scripts on remote machines, you'll need SSH access configured (e.g., SSH keys or password-based access, though SSH keys are recommended for security).
    
-   **AI API Keys (Optional but Recommended):**
    
    -   **Google Gemini API Key:** For AI script generation and analysis using Gemini models.
        
    -   **OpenAI API Key (ChatGPT):** For AI script generation and analysis using ChatGPT models.
        
    -   These keys are configured within the application's "Settings" page after launching.
        
-   **GitHub Personal Access Token (Optional but Recommended):**
    
    -   If you plan to push/pull scripts and pipelines from GitHub, you'll need a GitHub personal access token with appropriate repository permissions.
        
    -   This token and the target repository name are configured within the application's "Settings" page.
        
-   **Discord Webhook URL (Optional):**
    
    -   If you want to receive notifications via Discord. Configured in "Settings".
        

## How to Run the App

Once all prerequisites are met and installation steps are completed, you can run the Flask application:

```
flask run --host=0.0.0.0 --port=5055

```

This will start the Flask development server. You can then access the application in your web browser at `http://localhost:5055` (or the IP address of your server if running remotely, e.g., `http://100.116.246.164:5055`).
