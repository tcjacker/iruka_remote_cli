"""
Configuration management for Gemini CLI Docker Integration

This module provides centralized configuration management with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    """Configuration class with environment variable support."""
    
    # Main service configuration
    MAIN_SERVICE_HOST: str = os.getenv('MAIN_SERVICE_HOST', '127.0.0.1')
    MAIN_SERVICE_PORT: int = int(os.getenv('MAIN_SERVICE_PORT', '8081'))
    DEBUG: bool = os.getenv('DEBUG', '').lower() in ('true', '1', 'yes')
    
    # Docker configuration
    DOCKER_SOCKET_PATH: str = os.getenv('DOCKER_SOCKET_PATH', 'unix:///var/run/docker.sock')
    AGENT_IMAGE_TAG: str = os.getenv('AGENT_IMAGE_TAG', 'agent-service:latest')
    AGENT_INTERNAL_PORT: str = os.getenv('AGENT_INTERNAL_PORT', '5000')
    
    # Gemini API configuration
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    
    # Git configuration
    GIT_USER_NAME: str = os.getenv('GIT_USER_NAME', 'Gemini CLI User')
    GIT_USER_EMAIL: str = os.getenv('GIT_USER_EMAIL', 'user@example.com')
    
    # Demo configuration
    DEMO_REPO_URL: str = os.getenv('DEMO_REPO_URL', 'https://github.com/octocat/Hello-World.git')
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
    
    @classmethod
    def get_main_service_url(cls) -> str:
        """Get the main service URL."""
        return f"http://{cls.MAIN_SERVICE_HOST}:{cls.MAIN_SERVICE_PORT}"
    
    @classmethod
    def validate_config(cls) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check if Docker socket exists (on Unix systems)
        if cls.DOCKER_SOCKET_PATH.startswith('unix://'):
            socket_path = cls.DOCKER_SOCKET_PATH[7:]  # Remove 'unix://' prefix
            if not os.path.exists(socket_path):
                issues.append(f"Docker socket not found: {socket_path}")
        
        # Check port range
        if not (1024 <= cls.MAIN_SERVICE_PORT <= 65535):
            issues.append(f"Invalid port number: {cls.MAIN_SERVICE_PORT}")
        
        return issues
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (excluding sensitive data)."""
        print("🔧 Current Configuration:")
        print(f"   Main Service: {cls.get_main_service_url()}")
        print(f"   Debug Mode: {cls.DEBUG}")
        print(f"   Docker Image: {cls.AGENT_IMAGE_TAG}")
        print(f"   Log Level: {cls.LOG_LEVEL}")
        print(f"   Gemini API Key: {'✅ Set' if cls.GEMINI_API_KEY else '❌ Not set'}")
        
        issues = cls.validate_config()
        if issues:
            print("⚠️  Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")

# Global config instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def load_env_file(env_file: str = '.env') -> None:
    """Load environment variables from a .env file."""
    env_path = PROJECT_ROOT / env_file
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        
        # Reload config after setting environment variables
        global config
        config = Config()
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️  Environment file not found: {env_file}")

if __name__ == "__main__":
    # Test configuration
    load_env_file()
    config.print_config()
