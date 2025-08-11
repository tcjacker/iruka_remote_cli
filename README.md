# Iruka Remote

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A web-based UI for creating and managing isolated, Gemini-powered development environments within Docker containers. This tool is designed to streamline your AI-driven development workflow, allowing you to spin up fresh, clean coding environments tied to your Git repositories in seconds.

Each environment comes pre-configured with Git, Node.js, and the Gemini CLI, enabling you to go from a Git branch to a fully interactive AI coding session with just a few clicks.

## Core Features

- **Project-Based Management**: Organize your work into projects, each linked to a Git repository.
- **Isolated Docker Environments**: Create multiple, independent development environments (Docker containers) within each project.
- **Flexible Branching Strategy**:
    - Spin up an environment from an **existing remote branch** to fix a bug or collaborate on a feature.
    - Spin up an environment by creating a **new local and remote branch**, perfect for starting new features.
- **Automated Environment Setup**: Each new environment automatically:
    1.  Clones the project's Git repository.
    2.  Checks out the specified branch or creates a new one.
    3.  Pushes the new branch to the remote to enable immediate collaboration.
    4.  Comes pre-installed with `git`, `nodejs`, `npm`, and `@google/gemini-cli`.
- **Integrated Web Terminal**: A fully interactive `xterm.js` terminal in your browser, connected directly to the environment's shell.
- **Seamless Gemini CLI Integration**: Click on a running environment to be dropped directly into the Gemini CLI TUI, ready for AI-powered development.
- **Centralized Configuration**: Manage your Git and Gemini API tokens at the project level for secure and convenient access.

## Technology Stack

- **Frontend**:
    - **Framework**: React (with Vite)
    - **UI Library**: Material-UI
    - **Terminal**: Xterm.js
- **Backend**:
    - **Framework**: Python 3 with FastAPI
    - **Docker Interaction**: `docker-py`
    - **Real-time Communication**: WebSockets
    - **WSGI Server**: Uvicorn
- **Core Automation**:
    - Docker containerization
    - Shell scripting for environment provisioning

## Getting Started

### Prerequisites

- **Docker**: The Docker daemon must be running on the machine where you run the backend.
- **Python**: Python 3.10+ with `venv`.
- **Node.js**: Node.js 20+ with `npm`.
- **A Git repository** with a `Dockerfile` (a simple `ubuntu:latest` or `python:latest` base is a good start).

### Installation & Launch

You will need two separate terminal sessions to run the backend and frontend servers.

**1. Backend Server:**

```bash
# Navigate to the backend directory
cd ./backend

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\\Scripts\\activate

# Install the required Python packages
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload
```
The backend will be running on `http://localhost:8000`.

**2. Frontend Server:**

```bash
# Navigate to the frontend directory
cd ./frontend

# Install the required npm packages
npm install

# Run the Vite development server
npm run dev
```
The frontend will be accessible at `http://localhost:5173` (or the next available port).

## How to Use

1.  **Create a Project**:
    - Open the web UI in your browser.
    - Click on "New Project".
    - Fill in the project name and the **HTTPS URL** of your Git repository.
    - Optionally, add your Git Personal Access Token (required for private repos) and your Gemini API Key.
2.  **Open Project Workspace**:
    - Select your newly created project from the dropdown menu in the top header.
3.  **Manage Settings (Optional)**:
    - In the workspace, you can expand the "Project Settings" area to add or update your Git and Gemini API tokens at any time.
4.  **Create a New Environment**:
    - In the left sidebar, click the "**+ New**" button.
    - Give your environment a name (e.g., `feature-new-login`).
    - Choose your branching strategy:
        - **Create new branch**: A new branch named `feature/<your-env-name>` will be created locally and pushed to your remote repository.
        - **Use existing branch**: Select a branch from the dropdown of all available remote branches.
    - Select a base Docker image for the environment (e.g., `ubuntu:latest`).
    - Click "Create".
5.  **Connect to the Shell**:
    - Wait for the environment's status to become "running". This may take a few minutes as it installs dependencies.
    - Click on the running environment in the left sidebar.
    - The terminal on the right will connect and drop you directly into the Gemini CLI, ready for you to start coding.

## License

This project is licensed under the **GNU General Public License v3.0**.

Permissions of this strong copyleft license are conditioned on making available complete source code of licensed works and modifications, which include larger works using a licensed work, under the same license. Copyright and license notices must be preserved. Contributors provide an express grant of patent rights. See the [LICENSE](LICENSE) file for full details.
