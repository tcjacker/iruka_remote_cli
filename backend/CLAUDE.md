# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack web application called "Iruka Remote" that provides a web-based UI for creating and managing isolated, Gemini-powered development environments within Docker containers. The application allows users to spin up fresh, clean coding environments tied to their Git repositories in seconds.

### Technology Stack

- **Frontend**: React with Vite, Material-UI, Xterm.js for terminal emulation
- **Backend**: Python 3 with FastAPI, Docker SDK for Python, WebSockets
- **Infrastructure**: Docker containerization, Uvicorn WSGI server

### Core Features

- Project-based management linked to Git repositories
- Isolated Docker environments for each project
- Flexible branching strategy (create new branches or use existing ones)
- Automated environment setup with Git, Node.js, and Gemini CLI
- Integrated web terminal with xterm.js
- Seamless Gemini CLI integration
- Centralized configuration for Git and Gemini API tokens

## Common Development Commands

### Backend Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend runs on `http://localhost:8000`.

3. **Run with Docker** (if applicable):
   ```bash
   docker-compose up --build
   ```

### Frontend Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```
   The frontend runs on `http://localhost:5173`.

## Code Architecture

### Backend Structure

The backend is built with FastAPI and follows a modular structure:

- `app/main.py`: Entry point that initializes the FastAPI application and sets up routing
- `app/api.py`: Contains API endpoints for projects, environments, authentication, and Docker operations
- `app/auth.py`: Handles user authentication, password hashing, and JWT token management
- `app/services.py`: Contains business logic in two main services:
  - `ProjectService`: Manages project data persistence in JSON files
  - `DockerService`: Handles Docker container operations, image management, and shell sessions
- `app/websocket.py`: Manages WebSocket connections for real-time terminal communication
- `data/db.json`: JSON file used as a simple database for users and projects

### Key Components

1. **Authentication System**:
   - User registration and login with password hashing (bcrypt)
   - JWT-based token authentication
   - OAuth2 password flow implementation

2. **Project Management**:
   - CRUD operations for projects
   - Git repository integration
   - Environment management within projects

3. **Docker Environment Management**:
   - Container creation and lifecycle management
   - Automated environment setup with shell scripting
   - Image listing and management

4. **WebSocket Communication**:
   - Real-time terminal communication between browser and Docker containers
   - Shell session management

5. **Frontend Integration**:
   - RESTful API endpoints consumed by the React frontend
   - WebSocket endpoints for terminal sessions

## Development Notes

- Docker daemon must be running for the backend to work properly
- The application requires both Git and Gemini API tokens for full functionality
- Authentication is currently bypassed in the `get_current_user` function in `auth.py` for development purposes
- Environment names are sanitized for Docker compatibility using regex patterns
- The application uses a simple JSON file (`data/db.json`) for data persistence