# AI Ops Runner

    ## Summary

    AI Ops Runner is a web-based application designed to streamline server management and operations tasks. It provides a modern, clean interface to generate and execute scripts (Bash, Python, Ansible) on remote hosts, analyze the output using AI, and manage operational pipelines. The goal is to create a powerful, extensible platform that simplifies complex infrastructure tasks.

    ---

    ## Features Implemented

    * **Modular Flask Application:** Built using a blueprint architecture to keep features organized and easy to extend.
    * **Modern UI:** A dark-themed, sidebar-based layout inspired by modern cloud dashboards.
    * **Host Management:**
        * Add, edit, and delete hosts via the web UI.
        * Store detailed host information, including name, IP address, OS type, location, and description.
        * Dynamic forms that show Linux distribution options only when "Linux" is selected.
        * Live SSH connection testing for both new and existing hosts.
    * **Database Integration:** Uses Flask-SQLAlchemy and Flask-Migrate to manage a SQLite database for persistent storage.

    ---

    ## How to Install and Run

    Follow these steps to get the application running on your local machine.

    ### 1. Clone the Repository

    First, clone this repository to your local machine.

    ```bash
    git clone <your-repository-url>
    cd <repository-folder>

### 2\. Create a Virtual Environment

It is highly recommended to use a Python virtual environment to manage dependencies.

Bash

# Create the virtual environment
    python3 -m venv venv

    # Activate it (on Linux/macOS)
    source venv/bin/activate

    # On Windows, use:
    # venv\Scripts\activate

### 3\. Install Requirements

Install all the necessary Python packages using the `requirements.txt` file.

Bash

pip install -r requirements.txt

### 4\. Set up the Database

The application uses Flask-Migrate to manage database schemas. Run the following commands to initialize your database for the first time.

Bash

# Initialize the migration folder (only run this once per project)
    flask db init

    # Create the initial migration based on the models
    flask db migrate -m "Initial migration with hosts table"

    # Apply the migration to create the database and tables
    flask db upgrade

### 5\. Run the Application

You can now start the Flask development server.

Bash

flask run

The application will be running at `http://0.0.0.0:5055`. You can access it from your browser.

