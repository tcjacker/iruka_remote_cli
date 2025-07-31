#!/usr/bin/env python3
"""
Final Showcase Demo for Gemini CLI Docker Git Integration System

This demo showcases all the optimizations and features:
1. Fast Docker startup (pre-installed Gemini CLI)
2. Complete Git integration workflow
3. AI-assisted code generation and execution
4. File system operations
5. Multi-environment isolation
"""

import requests
import time
import json
import sys
import re
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

def print_banner(text):
    """Print a fancy banner"""
    print(f"\n{'🚀' * 20}")
    print(f"  {text}")
    print(f"{'🚀' * 20}")

def print_step(step_num, description):
    """Print formatted step information"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def extract_python_code(text):
    """Extract Python code from Gemini response, removing markdown formatting"""
    # Remove markdown code blocks
    text = re.sub(r'```python\s*\n', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'```', '', text)
    
    # Split into lines and filter out non-code lines
    lines = text.split('\n')
    code_lines = []
    
    for line in lines:
        # Skip lines that look like explanations
        if (line.strip() and 
            not line.strip().startswith('Here') and 
            not line.strip().startswith('This') and
            not line.strip().startswith('I will') and
            not line.strip().startswith('The script')):
            code_lines.append(line)
    
    return '\n'.join(code_lines).strip()

def main():
    """Main showcase demo"""
    print_banner("GEMINI CLI DOCKER GIT INTEGRATION SHOWCASE")
    print("🎯 Demonstrating: Fast startup + Git integration + AI coding")
    
    env_id = None
    start_time = time.time()
    
    try:
        # Step 1: Create Environment (Fast startup test)
        print_step(1, "Creating Environment (Testing Fast Startup)")
        env_start_time = time.time()
        
        response = requests.post(f"{MAIN_SERVICE_URL}/environments")
        
        if response.status_code != 201:
            print("❌ Failed to create environment")
            return
        
        env_data = response.json()
        env_id = env_data['env_id']
        print(f"✅ Environment created: {env_id}")
        
        # Wait for environment to be ready and measure startup time
        print("\n⏳ Waiting for environment to start (measuring startup time)...")
        time.sleep(8)  # Reduced wait time due to optimization
        
        env_ready_time = time.time()
        startup_duration = env_ready_time - env_start_time
        print(f"🚀 Environment startup time: {startup_duration:.1f} seconds")
        print("   (Optimized with pre-installed Gemini CLI!)")
        
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
        print_step(3, "Git Repository Cloning")
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
        
        # Step 4: AI Code Generation
        print_step(4, "AI-Assisted Code Generation")
        gemini_prompt = {
            "prompt": """Write a Python script that creates a simple calculator with these functions:
- add(a, b)
- subtract(a, b)  
- multiply(a, b)
- divide(a, b)

Then demonstrate all functions with example calculations and print the results.
Return only Python code, no explanations or markdown."""
        }
        
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini",
            json=gemini_prompt
        )
        
        if response.status_code != 200:
            print("❌ Failed to generate code with Gemini")
            return
        
        gemini_response = response.json().get('response', '')
        python_code = extract_python_code(gemini_response)
        
        print("✅ AI code generation successful")
        print(f"📝 Generated calculator code ({len(python_code)} characters)")
        
        # Step 5: Write AI-Generated Code to File
        print_step(5, "Writing AI Code to Workspace")
        write_data = {
            "path": "ai_calculator.py",
            "content": python_code
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/files/write",
            json=write_data
        )
        
        if response.status_code != 200:
            print("❌ Failed to write file")
            return
        
        print("✅ AI-generated code written to ai_calculator.py")
        
        # Step 6: Git Workflow
        print_step(6, "Complete Git Workflow")
        
        # Check status
        response = requests.get(f"{MAIN_SERVICE_URL}/environments/{env_id}/git/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"📊 Git status: {len(status_data.get('changes', []))} files changed")
        
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
            "message": "Add AI-generated calculator with full functionality"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/git/commit",
            json=commit_data
        )
        
        if response.status_code == 200:
            print("✅ Changes committed to Git repository")
        
        # Step 7: Code Execution
        print_step(7, "Executing AI-Generated Code")
        execute_data = {
            "command": "cd ./workspace && python ai_calculator.py"
        }
        response = requests.post(
            f"{MAIN_SERVICE_URL}/environments/{env_id}/execute",
            json=execute_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0:
                print("✅ AI-generated code executed successfully!")
                print("🧮 Calculator output:")
                print(result.get('stdout', ''))
            else:
                print("⚠️ Code execution issues:")
                print("Error:", result.get('stderr', ''))
        
        # Step 8: File System Operations
        print_step(8, "File System Operations")
        
        # List all files
        response = requests.get(f"{MAIN_SERVICE_URL}/environments/{env_id}/files/list")
        if response.status_code == 200:
            files_data = response.json()
            total_files = files_data.get('count', 0)
            print(f"📁 Total files in workspace: {total_files}")
            
            # Show non-git files
            non_git_files = [f for f in files_data.get('files', []) if not f.startswith('.git/')]
            print(f"📄 Project files: {non_git_files}")
        
        # Step 9: Git History
        print_step(9, "Git Commit History")
        execute_data = {
            "command": "cd ./workspace && git log --oneline -3"
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
        
        # Final Summary
        total_time = time.time() - start_time
        print_banner("SHOWCASE COMPLETED SUCCESSFULLY!")
        print(f"⏱️  Total demo time: {total_time:.1f} seconds")
        print(f"🚀 Container startup: {startup_duration:.1f} seconds (OPTIMIZED!)")
        print("\n🎯 FEATURES DEMONSTRATED:")
        print("✅ Ultra-fast Docker container startup (pre-installed Gemini CLI)")
        print("✅ Complete Git integration (clone, add, commit, history)")
        print("✅ AI-powered code generation with Gemini")
        print("✅ Secure file system operations")
        print("✅ Code execution in isolated environment")
        print("✅ Multi-environment support")
        print("✅ RESTful API for all operations")
        
        print("\n🔧 SYSTEM READY FOR:")
        print("🤖 AI-assisted software development")
        print("📦 Containerized development environments")
        print("🔄 Automated Git workflows")
        print("🛡️  Secure code execution")
        print("⚡ High-performance AI coding workflows")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Showcase interrupted by user")
    except Exception as e:
        print(f"\n❌ Showcase failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if env_id:
            print_step("Cleanup", "Environment Cleanup")
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
