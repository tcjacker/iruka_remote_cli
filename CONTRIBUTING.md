# Contributing to Gemini CLI Docker Integration

Thank you for your interest in contributing to this project! 🎉

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/auto_cli.git
   cd auto_cli
   ```
3. **Set up the development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🔧 Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Test your changes**:
   ```bash
   # Build the Docker image
   cd agent
   docker build -t agent-service:latest .
   cd ..
   
   # Run tests
   python demo_final_showcase.py
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## 📝 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Git Commit Messages
Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

### Docker Best Practices
- Minimize image layers
- Use specific version tags
- Clean up temporary files
- Follow security best practices

## 🧪 Testing

Before submitting a PR, ensure:
- [ ] Docker image builds successfully
- [ ] Main service starts without errors
- [ ] Demo scripts run successfully
- [ ] All API endpoints work as expected
- [ ] No security vulnerabilities introduced

## 📚 Documentation

When adding new features:
- Update the README.md if needed
- Add API documentation for new endpoints
- Include usage examples
- Update the demo scripts if applicable

## 🐛 Bug Reports

When reporting bugs, please include:
- Operating system and version
- Python version
- Docker version
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs

## 💡 Feature Requests

For feature requests:
- Describe the use case
- Explain the expected behavior
- Consider implementation complexity
- Discuss potential alternatives

## 🔒 Security

If you discover security vulnerabilities:
- **DO NOT** create a public issue
- Email the maintainers directly
- Provide detailed information about the vulnerability
- Allow time for the issue to be addressed before disclosure

## 📋 Areas for Contribution

We welcome contributions in these areas:

### 🚀 High Priority
- [ ] Web-based UI for easier interaction
- [ ] Enhanced error handling and logging
- [ ] Performance optimizations
- [ ] Additional AI provider integrations

### 🔧 Medium Priority
- [ ] Automated testing suite
- [ ] Configuration management improvements
- [ ] Better documentation and tutorials
- [ ] Code quality improvements

### 💡 Nice to Have
- [ ] Multi-language support beyond Python
- [ ] Advanced Git workflow automation
- [ ] Team collaboration features
- [ ] Monitoring and analytics

## 🤝 Code Review Process

1. All submissions require review
2. Maintainers will review PRs within 48-72 hours
3. Address feedback promptly
4. Ensure CI checks pass
5. Squash commits before merging

## 📞 Getting Help

- Create an issue for questions
- Join our discussions
- Check existing documentation
- Review demo scripts for examples

## 🎯 Project Goals

Keep these goals in mind when contributing:
- **Performance**: Fast startup and execution
- **Security**: Isolated and secure environments
- **Usability**: Simple and intuitive API
- **Reliability**: Robust error handling
- **Scalability**: Support for multiple environments

Thank you for contributing! 🙏
