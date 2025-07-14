# Fysseree AIOps v1.0.0 - Initial Release 🎉

**Release Date:** July 14, 2025

We are thrilled to announce the first official release of **Fysseree AIOps**, your all-in-one solution for intelligent DevOps and system administration. This version brings together a powerful suite of tools designed to automate workflows, manage infrastructure, and leverage AI to enhance operational efficiency.

## Overview

Fysseree AIOps is a web-based platform that empowers engineers to generate scripts using natural language, manage remote hosts, build complex automation pipelines, and handle administrative tasks like user management and data backups with ease. This initial release lays the foundation for a robust AIOps platform, now complete with a full REST API for programmatic access.

## ✨ Key Features in v1.0.0

* **Full REST API**: Programmatically manage all application resources (hosts, scripts, pipelines, etc.) via a comprehensive REST API, enabling integration with other tools and CI/CD systems.
* **Interactive API Documentation**: Explore and test API endpoints directly in the browser with an integrated, user-friendly API GUI.
* **AI-Powered Script Generation**: Instantly create Bash, Python, or Ansible scripts from simple English prompts using either Gemini or ChatGPT.
* **Centralized Host Management**: Add, edit, and manage your fleet of remote hosts. Test SSH connectivity directly from the UI.
* **Role-Based Access Control (RBAC)**: Secure your application with a flexible user and group management system. Define granular permissions (`view`, `full`, `none`) for different features.
* **API Key Management**: Generate and manage user-specific API keys for secure, authenticated access to the API.
* **Local and Google SSO Authentication**: Support for both traditional email/password logins and seamless single sign-on with Google.
* **Application Settings Management**: A centralized UI to configure all necessary API keys and application settings, with secrets masked for security.
* **Backup & Restore System**:
    * Create a complete backup of hosts, scripts, pipelines, and application settings into a single `.tar.gz` file.
    * Download backups directly.
    * Selectively restore components from a backup file with a safe preview step.
* **Modern, Responsive UI**: A clean, dark-themed interface built with Tailwind CSS for a great user experience on any device.

## 🚀 Getting Started

To get your instance of Fysseree AIOps up and running, follow these simple steps:

1.  **Clone the repository:**
    ```bash
    git clone <your_repository_url>
    cd ai-runner
    ```

2.  **Run the automated setup script:**
    This script handles everything from creating a virtual environment to setting up the database and creating the first admin user.
    ```bash
    chmod +x init-app.sh
    ./init-app.sh
    ```

3.  **Start the application:**
    ```bash
    source venv/bin/activate
    python3 run.py
    ```

Your application will be available at `http://127.0.0.1:5000`. Log in with the `admin` user and the password you set during the setup script.

## Known Issues

* The visual pipeline builder is present in the UI but the execution logic is still under development.
* Host credentials (passwords) are stored directly in the database. For production environments, integration with a dedicated secrets manager like HashiCorp Vault is recommended for future versions.

## What's Next?

We're just getting started! Here's a look at what we're planning for future releases:
* Full execution logic for the pipeline builder.
* Enhanced notification options.
* An operational dashboard with key metrics.
* Integration with more third-party services.

---

Thank you for using Fysseree AIOps. We welcome your feedback and contributions!

