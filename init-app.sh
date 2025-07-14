#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PYTHON_ENV_NAME="venv"
FLASK_APP_NAME="run.py"
REQUIREMENTS_FILE="requirements.txt"

# --- Functions ---
print_message() {
    echo "----------------------------------------"
    echo "$1"
    echo "----------------------------------------"
}

# --- Script Start ---
print_message "Starting Application Initialization"

# 1. Activate Virtual Environment
source "$PYTHON_ENV_NAME/bin/activate"
echo "Virtual environment activated."

# 2. Set Flask app environment variable
export FLASK_APP="$FLASK_APP_NAME"

# 3. Handle Database Migrations
print_message "Setting up the database..."

FRESH_INSTALL=false
# Check if the migrations directory exists. If not, initialize it.
if [ ! -d "migrations" ]; then
    echo "Migrations directory not found. Initializing..."
    flask db init
    FRESH_INSTALL=true
fi

# If this is a fresh install, we MUST create the first migration script.
if [ "$FRESH_INSTALL" = true ] ; then
    echo "Creating initial database migration script..."
    flask db migrate -m "Initial migration"
fi

# Apply any available migrations to the database.
echo "Applying database migrations..."
flask db upgrade

echo "setup admin user"
venv/bin/flask user create-admin admin

print_message "Application Initialization Complete! ✅"
echo "To activate the virtual environment, run: source $PYTHON_ENV_NAME/bin/activate"
