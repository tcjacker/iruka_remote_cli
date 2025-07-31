# 📁 Project Structure

This document provides an overview of the Gemini CLI Docker Git Integration project structure.

## 🏗️ Core Architecture

```
auto_cli/
├── 🚀 Main Entry Point
│   └── main.py                  # Main application entry point with CLI arguments
│
├── 🏗️ Core Services
│   ├── __init__.py              # Core module initialization
│   ├── main_service.py          # Main API gateway and environment manager
│   ├── build_image.py           # Docker image build automation
│   └── agent/
│       ├── agent.py             # Agent service running in Docker containers
│       ├── Dockerfile           # Optimized Docker image with pre-installed Gemini CLI
│       ├── startup.sh           # Container startup script with Git configuration
│       └── requirements.txt     # Python dependencies for agent service
│
├── 🎯 Demo Scripts
│   ├── __init__.py              # Demo module initialization
│   ├── demo_final_showcase.py   # Comprehensive system demonstration
│   ├── demo_git_integration.py  # Basic Git integration demo
│   ├── demo_git_integration_improved.py  # Enhanced Git demo with better prompts
│   └── demo_gemini_system.py    # Original Gemini system demo
│
├── 🧪 Tests
│   ├── __init__.py              # Test module initialization
│   ├── quick_test.py           # Quick functionality tests
│   └── test_*.py               # Various test scripts
│
├── 📚 Documentation
│   ├── README.md               # Main project documentation
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── PROJECT_STRUCTURE.md    # This file - project overview
│   ├── README_FINAL.md         # Legacy final documentation
│   └── README_GEMINI.md        # Legacy Gemini-specific docs
│
├── ⚙️ Configuration
│   ├── .env.example            # Environment variables template
│   ├── requirements.txt        # Main service Python dependencies
│   ├── .gitignore             # Git ignore rules
│   └── cleanup.sh             # System cleanup script
│
└── 📄 Legal
    └── LICENSE                 # MIT License
```

## 🔧 Key Components

### 🚀 Main Entry Point (`main.py`)
- **Purpose**: Application entry point with CLI argument parsing
- **Features**:
  - Command line argument handling
  - Environment variable configuration
  - Service startup and shutdown management
  - Debug mode support

### 🎯 Main Service (`core/main_service.py`)
- **Purpose**: Central API gateway and Docker environment manager
- **Port**: 8081 (configurable)
- **Features**:
  - Environment lifecycle management
  - Request routing to agent containers
  - Multi-environment support
  - Health monitoring

### 🐳 Agent Service (`core/agent/`)
- **Purpose**: Isolated execution environment with Gemini CLI and Git
- **Components**:
  - `agent.py`: Flask API server with Git/file operations
  - `Dockerfile`: Optimized image with pre-installed dependencies
  - `startup.sh`: Fast startup with Git configuration
- **Features**:
  - Pre-installed Gemini CLI (8s startup vs 60-90s)
  - Complete Git integration
  - Secure file system operations
  - Code execution capabilities

### 🎪 Demo Scripts
- **`demos/demo_final_showcase.py`**: Complete system demonstration
- **`demos/demo_git_integration*.py`**: Git-focused demonstrations
- **`demos/demo_gemini_system.py`**: Original system demo

## 🚀 Data Flow

```
User Request → Main Service (8081) → Agent Container (Dynamic Port) → Gemini CLI/Git
     ↑                ↓                        ↓                           ↓
   Response ← JSON Response ← Agent API Response ← Command Execution
```

## 🔒 Security Model

- **Container Isolation**: Each environment runs in isolated Docker containers
- **Path Validation**: Prevents directory traversal attacks
- **API Key Security**: Secure handling of Gemini API credentials
- **Workspace Isolation**: Separate workspaces per environment

## 📊 Performance Optimizations

1. **Docker Image Optimization**:
   - Pre-installed Gemini CLI
   - Node.js 20+ for compatibility
   - Cached dependencies
   - Minimal startup script

2. **Startup Time**: 8 seconds (vs 60-90 seconds original)

3. **Resource Management**:
   - Dynamic port allocation
   - Container lifecycle management
   - Automatic cleanup

## 🛠️ Development Workflow

1. **Setup**: `python -m venv venv && source venv/bin/activate`
2. **Install**: `pip install -r requirements.txt`
3. **Configure**: `cp .env.example .env` (add your Gemini API key)
4. **Build**: `cd core/agent && docker build -t agent-service:latest .`
5. **Run**: `python main.py`
6. **Test**: `python demos/demo_final_showcase.py`
7. **Cleanup**: `./cleanup.sh`

## 🔄 API Endpoints Overview

### Environment Management
- `POST /environments` - Create environment
- `DELETE /environments/{id}` - Delete environment
- `GET /health` - Health check

### AI Integration
- `POST /environments/{id}/gemini/configure` - Configure API key
- `POST /environments/{id}/gemini` - Generate code

### Git Operations
- `POST /environments/{id}/git/clone` - Clone repository
- `GET /environments/{id}/git/status` - Git status
- `POST /environments/{id}/git/add` - Stage files
- `POST /environments/{id}/git/commit` - Commit changes
- `POST /environments/{id}/git/push` - Push changes
- `POST /environments/{id}/git/pull` - Pull changes

### File System
- `GET /environments/{id}/files/list` - List files
- `GET /environments/{id}/files/read` - Read file
- `POST /environments/{id}/files/write` - Write file

### Execution
- `POST /environments/{id}/execute` - Execute commands

## 🎯 Use Cases

1. **AI-Assisted Development**: Generate and execute code with Gemini
2. **Git Workflow Automation**: Automated repository management
3. **Isolated Development**: Safe code execution in containers
4. **Multi-Project Management**: Concurrent isolated environments
5. **Educational Purposes**: Learn AI-assisted development workflows

## 🔮 Future Enhancements

- Web-based UI
- Multiple AI provider support
- Advanced Git workflow automation
- Team collaboration features
- Enhanced monitoring and logging

---

**This structure enables fast, secure, and scalable AI-assisted development workflows! 🚀**
