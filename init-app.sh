#!/bin/bash

# This script automates the initial setup of the AI-Runner Flask application.
# It creates a virtual environment, installs dependencies, sets up the database,
# and creates an initial admin user.
#
# Run this script from the root of the ai-runner project directory:
# ./init-app.sh

# Stop the script if any command fails
set -e

# --- Style Definitions for Output ---
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RED='\033[0;31m'
COLOR_NC='\033[0m' # No Color

echo -e "${COLOR_BLUE}=========================================${COLOR_NC}"
echo -e "${COLOR_BLUE}  AI-Runner Application Initial Setup  ${COLOR_NC}"
echo -e "${COLOR_BLUE}=========================================${COLOR_NC}"

# --- 1. Check for existing setup and ask to clean up ---
if [ -d "migrations" ] || [ -d "instance" ]; then
    echo -e "\n${COLOR_YELLOW}--- Detected existing database setup (migrations or instance folder) ---${COLOR_NC}"
    read -p "Do you want to remove it and start from scratch? (y/n) " -n 1 -r
    echo # Move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "\nCleaning up existing setup..."
        rm -rf venv migrations instance
        echo "Removed existing virtual environment, migrations, and instance folder."
    else
        echo -e "\n${COLOR_RED}Aborting setup. Your existing files have not been changed.${COLOR_NC}"
        exit 1
    fi
fi


# --- 2. Create Python Virtual Environment ---
echo -e "\n${COLOR_YELLOW}--- Step 1: Creating Python virtual environment in 'venv/' ---${COLOR_NC}"
# Re-check for venv in case it wasn't deleted above
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${COLOR_GREEN}Virtual environment created successfully.${COLOR_NC}"
else
    echo "Using existing virtual environment."
fi


# --- 3. Install Dependencies ---
# We will call the pip executable directly from the new venv
echo -e "\n${COLOR_YELLOW}--- Step 2: Installing dependencies from requirements.txt ---${COLOR_NC}"
venv/bin/pip install -r requirements.txt
echo -e "${COLOR_GREEN}Dependencies installed successfully.${COLOR_NC}"


# --- 4. Set FLASK_APP Environment Variable ---
# This export is only for the duration of this script
export FLASK_APP=app
echo -e "\n${COLOR_YELLOW}--- Step 3: Configuring Flask application environment ---${COLOR_NC}"
echo "FLASK_APP set to 'app'."


# --- 5. Initialize Database and Migrations ---
echo -e "\n${COLOR_YELLOW}--- Step 4: Initializing the database ---${COLOR_NC}"
# Use the flask executable from the venv
venv/bin/flask db init
echo "Database migrations initialized."

venv/bin/flask db migrate -m "Initial migration"
echo "Initial migration script created."

venv/bin/flask db upgrade
echo "Database schema applied."
echo -e "${COLOR_GREEN}Database setup complete.${COLOR_NC}"


# --- 6. Create Admin User ---
echo -e "\n${COLOR_YELLOW}--- Step 5: Creating the 'admin' user ---${COLOR_NC}"
echo "You will be prompted to enter and confirm a password for the admin user."
venv/bin/flask user create-admin admin
echo -e "${COLOR_GREEN}Admin user created successfully.${COLOR_NC}"


# --- 7. Final Instructions ---
echo -e "\n${COLOR_BLUE}=========================================${COLOR_NC}"
echo -e "${COLOR_GREEN}      SETUP COMPLETE! 🎉      ${COLOR_NC}"
echo -e "${COLOR_BLUE}=========================================${COLOR_NC}"
echo -e "\nTo run the application, follow these steps:"
echo -e "1. Activate the virtual environment: ${COLOR_YELLOW}source venv/bin/activate${COLOR_NC}"
echo -e "2. Run the app: ${COLOR_YELLOW}python3 run.py${COLOR_NC}"
echo -e "\nThen, open your browser and go to ${COLOR_BLUE}http://127.0.0.1:5000${COLOR_NC}"

