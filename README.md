# Fysseree AIOps: Your Intelligent DevOps Assistant

## Summary of App

Fysseree AIOps is a web-based application designed to streamline DevOps operations by integrating AI-powered script generation, execution, and analysis with host management and pipeline automation. It provides a centralized platform for managing infrastructure tasks, automating workflows, and leveraging artificial intelligence to enhance efficiency and reduce manual effort.

## Meaning of App Name

The name "Fysseree AIOps" signifies the core functionality of the application: "Fysseree" (meaning "intelligence" or "knowledge" in some contexts) combined with "AIOps" (Artificial Intelligence for IT Operations). It's a platform that **runs** various scripts and automated tasks, heavily leveraging **Artificial Intelligence** (AI) to assist in generating, analyzing, and executing these operations, implying an intelligent agent that executes commands and workflows to optimize IT operations.

## Purpose of App

The primary purpose of Fysseree AIOps is to empower DevOps engineers, system administrators, and developers with tools to:

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
-   **User Management (RBAC):**
    -   Local user accounts with username and password.
    -   Role-Based Access Control (RBAC) with Admin, Engineer, and Viewer groups.
    -   Ability to add, edit, and delete users and groups.
    -   Define feature-level permissions (Full Access, View Access, No Access) for each group.

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

## Install and First-Time Setup

To install and set up Fysseree AIOps for the first time, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ai-runner
    ```

2.  **Run the Initialization Script:**
    The project includes a script to automate the entire setup process. First, make it executable:
    ```bash
    chmod +x init-app.sh
    ```
    Then, run the script:
    ```bash
    ./init-app.sh
    ```
    This script will:
    - Create a Python virtual environment (`venv`).
    - Install all required dependencies from `requirements.txt`.
    - Initialize the database and run migrations.
    - Create an `admin` user and prompt you to set a password.

## How to Run the App

After the initial setup is complete, follow these steps to run the application:

1.  **Activate the virtual environment:**
    (You need to do this every time you open a new terminal for this project)
    ```bash
    source venv/bin/activate
    ```

2.  **Start the web server:**
    ```bash
    python3 run.py
    ```

You can now access the application in your web browser at **http://127.0.0.1:5000**. Log in with the `admin` username and the password you set during setup.

