# 🚀 Gemini CLI Docker Git Integration

A high-performance, containerized AI-assisted development system that integrates Google's Gemini AI with Git workflows in isolated Docker environments.

## ✨ Features

- **⚡ Ultra-fast startup**: Optimized Docker containers with pre-installed Gemini CLI (8s vs 60-90s)
- **🤖 AI-powered coding**: Generate, modify, and execute code using Google Gemini
- **🔄 Complete Git integration**: Clone, commit, push, and manage repositories
- **🛡️ Secure isolation**: Each environment runs in its own Docker container
- **📡 RESTful API**: Full HTTP API for all operations
- **🔧 Multi-environment**: Support for concurrent isolated development environments

## 🏗️ Architecture

```
Frontend/Client → Main Service (Flask) → Agent Containers (Docker) → Gemini CLI + Git
```

- **Main Service** (`main_service.py`): Central API gateway and environment manager
- **Agent Containers**: Isolated Docker environments with Gemini CLI and Git
- **RESTful API**: Complete HTTP API for all operations

## 🚀 Quick Start

### Prerequisites

- Docker
- Python 3.8+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd auto_cli
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

4. **Build Docker image**
   ```bash
   cd core/agent
   docker build -t agent-service:latest .
   cd ../..
   ```

5. **Start the main service**
   ```bash
   python main.py
   ```

## 📖 Usage

### Basic Workflow

1. **Create an environment**
   ```bash
   curl -X POST http://localhost:8081/environments
   ```

2. **Configure Gemini API key**
   ```bash
   curl -X POST http://localhost:8081/environments/{env_id}/gemini/configure \
     -H "Content-Type: application/json" \
     -d '{"api_key": "your_api_key"}'
   ```

3. **Clone a repository**
   ```bash
   curl -X POST http://localhost:8081/environments/{env_id}/git/clone \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/user/repo.git", "target_dir": "./workspace"}'
   ```

4. **Generate code with AI**
   ```bash
   curl -X POST http://localhost:8081/environments/{env_id}/gemini \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a Python function to calculate fibonacci numbers"}'
   ```

5. **Write and execute code**
   ```bash
   # Write file
   curl -X POST http://localhost:8081/environments/{env_id}/files/write \
     -H "Content-Type: application/json" \
     -d '{"path": "fibonacci.py", "content": "generated_code_here"}'
   
   # Execute code
   curl -X POST http://localhost:8081/environments/{env_id}/execute \
     -H "Content-Type: application/json" \
     -d '{"command": "python fibonacci.py"}'
   ```

6. **Commit changes**
   ```bash
   # Add files
   curl -X POST http://localhost:8081/environments/{env_id}/git/add \
     -H "Content-Type: application/json" \
     -d '{"files": ["."]}'
   
   # Commit
   curl -X POST http://localhost:8081/environments/{env_id}/git/commit \
     -H "Content-Type: application/json" \
     -d '{"message": "Add AI-generated fibonacci function"}'
   ```

### Demo Scripts

Run the comprehensive demo to see all features:

```bash
python demos/demo_final_showcase.py
```

## 🔧 API Reference

### Environment Management
- `POST /environments` - Create new environment
- `DELETE /environments/{id}` - Delete environment
- `GET /health` - Health check

### Gemini AI Integration
- `POST /environments/{id}/gemini/configure` - Configure API key
- `POST /environments/{id}/gemini` - Generate code with AI

### Git Operations
- `POST /environments/{id}/git/clone` - Clone repository
- `GET /environments/{id}/git/status` - Check Git status
- `POST /environments/{id}/git/add` - Add files to staging
- `POST /environments/{id}/git/commit` - Commit changes
- `POST /environments/{id}/git/push` - Push to remote
- `POST /environments/{id}/git/pull` - Pull from remote

### File System Operations
- `GET /environments/{id}/files/list` - List files
- `GET /environments/{id}/files/read` - Read file content
- `POST /environments/{id}/files/write` - Write file content

### Code Execution
- `POST /environments/{id}/execute` - Execute shell commands

## 🛡️ Security Features

- **Container Isolation**: Each environment runs in isolated Docker containers
- **Path Validation**: Prevents directory traversal attacks
- **API Key Security**: Secure handling of Gemini API keys
- **Workspace Isolation**: Each environment has its own workspace

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options.

### Docker Optimization

The system is optimized for fast startup:
- Gemini CLI is pre-installed in the Docker image
- Node.js 20+ for compatibility
- Minimal startup script
- Cached dependencies

## 📊 Performance

- **Container startup**: ~8 seconds (optimized from 60-90 seconds)
- **Complete AI workflow**: ~25 seconds (create → code → commit → execute)
- **Concurrent environments**: Supports multiple isolated environments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

[Add your license here]

## 🆘 Troubleshooting

### Common Issues

1. **Docker build fails**: Ensure Docker is running and you have sufficient disk space
2. **Gemini API errors**: Verify your API key is valid and has sufficient quota
3. **Port conflicts**: Change `MAIN_SERVICE_PORT` in `.env` if port 8081 is in use

### Cleanup

To stop all services and clean up containers:

```bash
./cleanup.sh
```

## 🔮 Future Enhancements

- [ ] Web-based UI
- [ ] Multiple AI provider support
- [ ] Advanced Git workflow automation
- [ ] Code review integration
- [ ] Team collaboration features

---

**Built with ❤️ for AI-assisted development**
