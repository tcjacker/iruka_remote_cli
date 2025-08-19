# Project Overview

This project, "Iruka Remote," is a web-based UI for creating and managing isolated, AI-powered development environments within Docker containers. It's designed to streamline AI-driven development workflows by allowing users to quickly spin up fresh coding environments tied to their Git repositories.

## Technology Stack

-   **Frontend**:
    -   **Framework**: React (with Vite)
    -   **UI Library**: Material-UI
    -   **Terminal**: Xterm.js
-   **Backend**:
    -   **Framework**: Python 3 with FastAPI
    -   **Docker Interaction**: `docker-py`
    -   **Real-time Communication**: WebSockets
    -   **WSGI Server**: Uvicorn
-   **Core Automation**:
    -   Docker containerization
    -   Shell scripting for environment provisioning

## Building and Running

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

## Development Conventions

-   **Linting**: The frontend uses ESLint for code linting. Run `npm run lint` in the `frontend` directory to check for issues.
-   **Dependencies**: Backend dependencies are managed with `pip` and `requirements.txt`. Frontend dependencies are managed with `npm` and `package.json`.
