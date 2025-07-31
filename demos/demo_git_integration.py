#!/usr/bin/env python3
"""
Git Integration Demo for Gemini CLI Docker System

This script demonstrates the complete Git integration workflow:
1. Create environment and configure Gemini API key
2. Clone a GitHub repository
3. List and read files
4. Use Gemini to generate code
5. Write code to workspace
6. Add, commit, and optionally push changes
7. Execute generated code
8. Clean up environment

Usage:
    python demo_git_integration.py
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

def print_response(response, title="Response"):
    """Print formatted response"""
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")

def wait_for_service(url, max_attempts=10, delay=2):
    """Wait for a service to become available"""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"Service not ready, waiting {delay} seconds... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)
    
    return False

def main():
    """Main demo function"""
    print("🚀 Gemini CLI Docker Git Integration Demo")
    print("=========================================")
    
    # Check if main service is running
    if not wait_for_service(MAIN_SERVICE_URL):
        print("❌ Main service is not available. Please start it first:")
        print("   python main_service.py")
        sys.exit(1)
    
    env_id = None
    
    try:
        # Step 1: Create Environment
        print_step(1, "Creating Environment")
        response = requests.post(f"{MAIN_SERVICE_URL}/environments")
        print_response(response, "Create Environment")
        
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
        print_response(response, "Configure API Key")
        
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
        print_response(response, "Git Clone")
        
        if response.status_code != 200:
            print("❌ Failed to clone repository")
            return
        
        print("✅ Repository cloned successfully")
        
        # Step 4: List Files in Workspace
        print_step(4, "Listing Files in Workspace")
        response = requests.get(f"{MAIN_SERVICE_URL}/environments/{env_id}/files/list")
        print_response(response, "List Files")
        
        if response.status_code == 200:
            files = response.json().get('files', [])
            print(f"✅ Found {len(files)} files in workspace")
            for file in files[:5]:  # Show first 5 files
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
        
        # Step 5: Read README file (if exists)
        print_step(5, "Reading README File")
        response = requests.get(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/files/read",
            params={"path": "README"}
        )
        if response.status_code == 200:
            content = response.json().get('content', '')
            print("✅ README content:")
            print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print("ℹ️ No README file found")
        
        # Step 6: Use Gemini to Generate Python Code
        print_step(6, "Generating Python Code with Gemini")
        gemini_prompt = {
            "prompt": "Create a simple Python script that prints 'Hello from Gemini CLI!' and shows the current date and time. Make it colorful with some emojis."
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini",
            json=gemini_prompt
        )
        print_response(response, "Gemini Code Generation")
        
        if response.status_code != 200:
            print("❌ Failed to generate code with Gemini")
            return
        
        gemini_response = response.json().get('response', '')
        print("✅ Code generated successfully")
        
        # Extract Python code from Gemini response
        # Look for code blocks
        code_start = gemini_response.find('```python')
        if code_start == -1:
            code_start = gemini_response.find('```')
        
        if code_start != -1:
            code_start = gemini_response.find('\n', code_start) + 1
            code_end = gemini_response.find('```', code_start)
            if code_end != -1:
                python_code = gemini_response[code_start:code_end].strip()
            else:
                python_code = gemini_response[code_start:].strip()
        else:
            # If no code blocks found, use the entire response
            python_code = gemini_response
        
        print(f"📝 Generated code:\n{python_code}")
        
        # Step 7: Write Generated Code to File
        print_step(7, "Writing Generated Code to File")
        write_data = {
            "path": "gemini_generated.py",
            "content": python_code
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/files/write",
            json=write_data
        )
        print_response(response, "Write File")
        
        if response.status_code != 200:
            print("❌ Failed to write file")
            return
        
        print("✅ Code written to gemini_generated.py")
        
        # Step 8: Check Git Status
        print_step(8, "Checking Git Status")
        response = requests.get(f"{MAIN_SERVICE_URL}/environments/{env_id}/git/status")
        print_response(response, "Git Status")
        
        # Step 9: Add Files to Git
        print_step(9, "Adding Files to Git")
        add_data = {"files": ["."]}
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/add",
            json=add_data
        )
        print_response(response, "Git Add")
        
        if response.status_code == 200:
            print("✅ Files added to Git staging area")
        
        # Step 10: Commit Changes
        print_step(10, "Committing Changes")
        commit_data = {
            "message": "Add Gemini-generated Python script"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/commit",
            json=commit_data
        )
        print_response(response, "Git Commit")
        
        if response.status_code == 200:
            print("✅ Changes committed successfully")
        
        # Step 11: Execute Generated Code
        print_step(11, "Executing Generated Code")
        execute_data = {
            "command": "cd ./workspace && python gemini_generated.py"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/execute",
            json=execute_data
        )
        print_response(response, "Execute Code")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0:
                print("✅ Code executed successfully!")
                print("Output:", result.get('stdout', ''))
            else:
                print("⚠️ Code execution had issues:")
                print("Error:", result.get('stderr', ''))
        
        # Optional Step 12: Push Changes (commented out for demo)
        print_step(12, "Push Changes (Optional - Skipped)")
        print("ℹ️ Push operation skipped in demo (would require authentication)")
        print("   To push changes, you would use:")
        print(f"   POST {MAIN_SERVICE_URL}/environments/{env_id}/git/push")
        
        print("\n🎉 Git Integration Demo Completed Successfully!")
        print("="*60)
        print("Summary of what we accomplished:")
        print("✅ Created isolated Docker environment")
        print("✅ Configured Gemini API key")
        print("✅ Cloned GitHub repository")
        print("✅ Listed and read files")
        print("✅ Generated Python code with Gemini")
        print("✅ Wrote code to workspace")
        print("✅ Added and committed changes to Git")
        print("✅ Executed generated code")
        print("\nThe system is ready for AI-assisted development workflows!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
    finally:
        # Step 13: Clean Up Environment
        if env_id:
            print_step(13, "Cleaning Up Environment")
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
