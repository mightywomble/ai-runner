
# AI Ops Runner

## Summary

AI Ops Runner is a web-based application designed to streamline server management and operations tasks. It provides a modern, clean interface to generate and execute scripts (Bash, Python, Ansible) on remote hosts, analyze the output using AI, and manage operational pipelines. The goal is to create a powerful, extensible platform that simplifies complex infrastructure tasks.

----------

## Features Implemented

-   **Modular Flask Application:** Built using a blueprint architecture to keep features organized and easy to extend.

-   **Modern UI:** A dark-themed, sidebar-based layout inspired by modern cloud dashboards.

-   **Host Management:**

    -   Add, edit, and delete hosts via the web UI.

    -   Store detailed host information, including name, IP address, OS type, location, and description.

    -   Dynamic forms that show Linux distribution options only when "Linux" is selected.

    -   Live SSH connection testing for both new and existing hosts.

-   **Database Integration:** Uses Flask-SQLAlchemy and Flask-Migrate to manage a SQLite database for persistent storage.


----------

## How to Install and Run

Follow these steps to get the application running on your local machine.

### 1. Clone the Repository

First, clone this repository to your local machine.

Bash
