#!/usr/bin/env python3
"""
Improved Git Integration Demo for Gemini CLI Docker System

This demo uses a more specific prompt to get better code generation from Gemini.
"""

import requests
import time
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import load_env_file, get_config

# Load configuration
load_env_file()
config = get_config()

# Configuration
MAIN_SERVICE_URL = config.get_main_service_url()
GEMINI_API_KEY = config.GEMINI_API_KEY
DEMO_REPO_URL = config.DEMO_REPO_URL

def print_step(step_num, description):
    """Print formatted step information"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def main():
    """Main demo function with improved Gemini prompt"""
    print("🚀 Improved Gemini CLI Docker Git Integration Demo")
    print("=================================================")
    
    env_id = None
    
    try:
        # Step 1: Create Environment
        print_step(1, "Creating Environment")
        response = requests.post(f"{MAIN_SERVICE_URL}/environments")
        
        if response.status_code != 201:
            print("❌ Failed to create environment")
            return
        
        env_data = response.json()
        env_id = env_data['env_id']
        print(f"✅ Environment created: {env_id}")
        
        # Wait for environment to be ready
        print("\n⏳ Waiting for environment to start...")
        time.sleep(10)
        
        # Step 2: Configure Gemini API Key
        print_step(2, "Configuring Gemini API Key")
        config_data = {"api_key": GEMINI_API_KEY}
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini/configure",
            json=config_data
        )
        
        if response.status_code != 200:
            print("❌ Failed to configure API key")
            return
        
        print("✅ API key configured successfully")
        
        # Step 3: Clone Repository
        print_step(3, "Cloning GitHub Repository")
        clone_data = {
            "repo_url": DEMO_REPO_URL,
            "target_dir": "./workspace"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/clone",
            json=clone_data
        )
        
        if response.status_code != 200:
            print("❌ Failed to clone repository")
            return
        
        print("✅ Repository cloned successfully")
        
        # Step 4: Use Gemini to Generate Python Code with Better Prompt
        print_step(4, "Generating Python Code with Gemini (Improved Prompt)")
        gemini_prompt = {
            "prompt": """Please write only the Python code (no explanations) for a script that:
1. Prints 'Hello from Gemini CLI!' with colorful emojis
2. Shows the current date and time
3. Uses ANSI color codes for colorful output

Return ONLY the Python code, no markdown formatting, no explanations."""
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini",
            json=gemini_prompt
        )
        
        if response.status_code != 200:
            print("❌ Failed to generate code with Gemini")
            return
        
        gemini_response = response.json().get('response', '')
        print("✅ Code generated successfully")
        print(f"📝 Generated code:\n{gemini_response}")
        
        # Step 5: Write Generated Code to File
        print_step(5, "Writing Generated Code to File")
        write_data = {
            "path": "hello_gemini.py",
            "content": gemini_response
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/files/write",
            json=write_data
        )
        
        if response.status_code != 200:
            print("❌ Failed to write file")
            return
        
        print("✅ Code written to hello_gemini.py")
        
        # Step 6: Add and Commit Changes
        print_step(6, "Adding and Committing Changes")
        
        # Add files
        add_data = {"files": ["."]}
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/add",
            json=add_data
        )
        
        if response.status_code == 200:
            print("✅ Files added to Git staging area")
        
        # Commit changes
        commit_data = {
            "message": "Add colorful Hello Gemini script"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/commit",
            json=commit_data
        )
        
        if response.status_code == 200:
            print("✅ Changes committed successfully")
        
        # Step 7: Execute Generated Code
        print_step(7, "Executing Generated Code")
        execute_data = {
            "command": "cd ./workspace && python hello_gemini.py"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/execute",
            json=execute_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0:
                print("✅ Code executed successfully!")
                print("🎨 Output:")
                print(result.get('stdout', ''))
            else:
                print("⚠️ Code execution had issues:")
                print("Error:", result.get('stderr', ''))
        
        # Step 8: Show Git Log
        print_step(8, "Showing Git Commit History")
        execute_data = {
            "command": "cd ./workspace && git log --oneline -5"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/execute",
            json=execute_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0:
                print("📜 Recent commits:")
                print(result.get('stdout', ''))
        
        print("\n🎉 Improved Git Integration Demo Completed!")
        print("="*60)
        print("🚀 System Features Demonstrated:")
        print("✅ Fast Docker container startup (with pre-installed Gemini CLI)")
        print("✅ Git repository cloning and management")
        print("✅ AI code generation with Gemini")
        print("✅ File system operations")
        print("✅ Git workflow (add, commit)")
        print("✅ Code execution in isolated environment")
        print("\n🔧 Ready for production AI-assisted development!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
    finally:
        # Clean up environment
        if env_id:
            print_step("Cleanup", "Cleaning Up Environment")
            try:
                response = requests.delete(f"{MAIN_SERVICE_URL}/environments/{env_id}")
                if response.status_code == 200:
                    print("✅ Environment cleaned up successfully")
                else:
                    print("⚠️ Failed to clean up environment")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {str(e)}")

if __name__ == "__main__":
    main()
