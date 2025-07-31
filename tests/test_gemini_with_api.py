#!/usr/bin/env python3
"""
Enhanced test script for Gemini CLI integration with API key support.
This script demonstrates how to use the main service API to interact with Gemini CLI.
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import load_env_file, get_config

# Load configuration
load_env_file()
config = get_config()

# Configuration
BASE_URL = config.get_main_service_url()
GEMINI_API_KEY = config.GEMINI_API_KEY

def create_environment():
    """Create a new environment."""
    print("Creating new environment...")
    response = requests.post(f"{BASE_URL}/environments")
    if response.status_code in [200, 201]:
        data = response.json()
        env_id = data['env_id']
        print(f"Environment created successfully: {env_id}")
        return env_id
    else:
        print(f"Failed to create environment: {response.status_code} - {response.text}")
        return None

def configure_api_key(env_id, api_key):
    """Configure Gemini API key for the environment."""
    print(f"Configuring API key for environment {env_id}...")
    response = requests.post(
        f"{BASE_URL}/environments/{env_id}/gemini/configure",
        json={"api_key": api_key}
    )
    if response.status_code == 200:
        print("API key configured successfully")
        return True
    else:
        print(f"Failed to configure API key: {response.text}")
        return False

def check_gemini_status(env_id):
    """Check Gemini CLI status."""
    print(f"Checking Gemini status in environment {env_id}...")
    response = requests.get(f"{BASE_URL}/environments/{env_id}/gemini/status")
    if response.status_code == 200:
        data = response.json()
        print(f"Gemini status: {data}")
        return data.get('gemini_running', False)
    else:
        print(f"Failed to check Gemini status: {response.text}")
        return False

def send_prompt(env_id, prompt, api_key=None):
    """Send a prompt to Gemini CLI."""
    print(f"Sending prompt to Gemini in environment {env_id}...")
    print(f"Prompt: {prompt}")
    
    payload = {"prompt": prompt}
    if api_key:
        payload["api_key"] = api_key
    
    response = requests.post(
        f"{BASE_URL}/environments/{env_id}/gemini",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data.get('response', 'No response')}")
        return True
    else:
        print(f"Failed to send prompt: {response.text}")
        return False

def restart_gemini(env_id):
    """Restart Gemini CLI."""
    print(f"Restarting Gemini in environment {env_id}...")
    response = requests.post(f"{BASE_URL}/environments/{env_id}/gemini/restart")
    if response.status_code == 200:
        print("Gemini restarted successfully")
        return True
    else:
        print(f"Failed to restart Gemini: {response.text}")
        return False

def delete_environment(env_id):
    """Delete the environment."""
    print(f"Deleting environment {env_id}...")
    response = requests.delete(f"{BASE_URL}/environments/{env_id}")
    if response.status_code == 200:
        print("Environment deleted successfully")
        return True
    else:
        print(f"Failed to delete environment: {response.text}")
        return False

def main():
    """Main test function."""
    print("=== Enhanced Gemini CLI Integration Test ===")
    
    # Check if API key is provided
    if GEMINI_API_KEY == "your-gemini-api-key-here":
        print("\n⚠️  WARNING: Please set your actual Gemini API key in the GEMINI_API_KEY variable")
        print("You can get an API key from: https://makersuite.google.com/app/apikey")
        
        # Ask user if they want to continue with a demo (will fail but show the flow)
        choice = input("\nDo you want to continue with a demo (will show API key error)? (y/n): ")
        if choice.lower() != 'y':
            print("Exiting. Please set your API key and try again.")
            return
        
        # Use a dummy key for demo
        api_key = "demo-key"
    else:
        api_key = GEMINI_API_KEY
    
    # Create environment
    env_id = create_environment()
    if not env_id:
        return
    
    # Wait for container to start
    print("Waiting for container to start...")
    time.sleep(15)
    
    # Configure API key
    if not configure_api_key(env_id, api_key):
        print("Failed to configure API key, but continuing with tests...")
    
    # Check Gemini status
    check_gemini_status(env_id)
    
    # Test prompts
    test_prompts = [
        "Hello, how are you?",
        "What is Python programming language?",
        "Tell me a short joke",
        "What is 15 + 27?"
    ]
    
    for prompt in test_prompts:
        print(f"\n--- Testing prompt: {prompt} ---")
        send_prompt(env_id, prompt, api_key)
        time.sleep(2)  # Small delay between requests
    
    # Test restart functionality
    print("\n--- Testing Gemini restart ---")
    restart_gemini(env_id)
    time.sleep(3)
    check_gemini_status(env_id)
    
    # Clean up
    print("\n--- Cleaning up ---")
    delete_environment(env_id)
    
    print("\n=== Test completed ===")
    print("\nIf you saw API key errors, make sure to:")
    print("1. Get a Gemini API key from: https://makersuite.google.com/app/apikey")
    print("2. Set the GEMINI_API_KEY variable in this script")
    print("3. Run the test again")

if __name__ == "__main__":
    main()
