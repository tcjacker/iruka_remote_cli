import subprocess
import json
import os
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global variable to store Gemini CLI process
gemini_process = None

def start_gemini_cli():
    """Start the Gemini CLI process if not already running"""
    global gemini_process
    if gemini_process is None or gemini_process.poll() is not None:
        try:
            # Start gemini CLI in interactive mode
            gemini_process = subprocess.Popen(
                ['gemini'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            logging.info("Gemini CLI started successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to start Gemini CLI: {e}")
            return False
    return True

def configure_gemini_api_key(api_key):
    """Configure Gemini API key"""
    try:
        # Create .gemini directory if it doesn't exist
        gemini_dir = os.path.expanduser('~/.gemini')
        os.makedirs(gemini_dir, exist_ok=True)
        
        # Create settings.json with API key
        settings_file = os.path.join(gemini_dir, 'settings.json')
        settings = {
            "apiKey": api_key
        }
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        logging.info("Gemini API key configured successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to configure API key: {e}")
        return False

def get_configured_api_key():
    """Get the configured API key from settings file"""
    try:
        gemini_dir = os.path.expanduser('~/.gemini')
        settings_file = os.path.join(gemini_dir, 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('apiKey')
    except Exception as e:
        logging.error(f"Failed to read API key from settings: {e}")
    return None

def send_to_gemini(prompt, api_key=None):
    """Send a prompt to Gemini CLI and get response"""
    try:
        # Set up environment with API key
        env = os.environ.copy()
        
        # If no API key provided, try to get from configured settings
        if not api_key:
            api_key = get_configured_api_key()
        
        if api_key:
            env['GEMINI_API_KEY'] = api_key
        else:
            # No API key available
            return {"error": "API key required. Please configure API key first using /gemini/configure endpoint."}
        
        # Use gemini CLI with proper -p flag for prompt
        result = subprocess.run(
            ['gemini', '-p', prompt],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            check=False,
            env=env
        )
        
        if result.returncode == 0:
            response = result.stdout.strip()
            if response:
                return {"response": response}
            else:
                return {"response": "Gemini CLI returned empty response"}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logging.error(f"Gemini CLI error: {error_msg}")
            
            # Check if it's an API key issue
            if "Auth method" in error_msg or "GEMINI_API_KEY" in error_msg:
                return {"error": "API key required. Please provide a valid Gemini API key."}
            
            return {"error": f"Gemini CLI error: {error_msg}"}
        
    except subprocess.TimeoutExpired:
        logging.error("Gemini CLI request timed out")
        return {"error": "Request timed out"}
    except Exception as e:
        logging.error(f"Error calling Gemini CLI: {e}")
        return {"error": str(e)}

@app.route('/gemini', methods=['POST'])
def gemini_chat():
    """Send a prompt to Gemini CLI"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400
        
        prompt = data['prompt']
        api_key = data.get('api_key')  # Optional API key in request
        
        result = send_to_gemini(prompt, api_key)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error in gemini_chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gemini/configure', methods=['POST'])
def configure_gemini():
    """Configure Gemini API key"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"error": "Missing 'api_key' in request"}), 400
        
        api_key = data['api_key']
        if configure_gemini_api_key(api_key):
            return jsonify({"message": "API key configured successfully"})
        else:
            return jsonify({"error": "Failed to configure API key"}), 500
    
    except Exception as e:
        logging.error(f"Error in configure_gemini: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gemini/status', methods=['GET'])
def gemini_status():
    """Check if Gemini CLI is running"""
    global gemini_process
    is_running = gemini_process is not None and gemini_process.poll() is None
    return jsonify({"gemini_running": is_running})

@app.route('/gemini/restart', methods=['POST'])
def restart_gemini():
    """Restart Gemini CLI"""
    global gemini_process
    if gemini_process is not None:
        try:
            gemini_process.terminate()
            gemini_process.wait()
        except:
            pass
        gemini_process = None
    
    success = start_gemini_cli()
    return jsonify({"restarted": success})

@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute general shell commands"""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "Invalid request. 'command' field is required."}), 400

    command = data['command']
    try:
        # Execute the command in the shell
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False  # Do not raise exception for non-zero exit codes
        )
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== Git Integration Functions ====================

@app.route('/git/clone', methods=['POST'])
def git_clone():
    """Clone a Git repository"""
    data = request.get_json()
    if not data or 'repo_url' not in data:
        return jsonify({"error": "Invalid request. 'repo_url' field is required."}), 400
    
    repo_url = data['repo_url']
    target_dir = data.get('target_dir', './workspace')
    
    try:
        # Create workspace directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Clone the repository
        result = subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "message": "Repository cloned successfully",
                "target_dir": target_dir,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git clone failed",
                "stderr": result.stderr,
                "returncode": result.returncode
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/status', methods=['GET'])
def git_status():
    """Get Git status of the workspace"""
    workspace_dir = request.args.get('dir', './workspace')
    
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "changes": result.stdout.strip().split('\n') if result.stdout.strip() else [],
                "has_changes": bool(result.stdout.strip())
            })
        else:
            return jsonify({
                "error": "Git status failed",
                "stderr": result.stderr
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/add', methods=['POST'])
def git_add():
    """Add files to Git staging area"""
    data = request.get_json()
    workspace_dir = data.get('dir', './workspace')
    files = data.get('files', ['.'])  # Default to add all files
    
    try:
        cmd = ['git', 'add'] + files
        result = subprocess.run(
            cmd,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "message": "Files added to staging area",
                "files": files
            })
        else:
            return jsonify({
                "error": "Git add failed",
                "stderr": result.stderr
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/commit', methods=['POST'])
def git_commit():
    """Commit changes to Git repository"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400
    
    workspace_dir = data.get('dir', './workspace')
    commit_message = data['message']
    
    try:
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "message": "Changes committed successfully",
                "commit_message": commit_message,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git commit failed",
                "stderr": result.stderr
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/push', methods=['POST'])
def git_push():
    """Push changes to remote repository"""
    data = request.get_json() or {}
    workspace_dir = data.get('dir', './workspace')
    branch = data.get('branch', 'main')
    
    try:
        result = subprocess.run(
            ['git', 'push', 'origin', branch],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "message": "Changes pushed successfully",
                "branch": branch,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git push failed",
                "stderr": result.stderr
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/pull', methods=['POST'])
def git_pull():
    """Pull latest changes from remote repository"""
    data = request.get_json() or {}
    workspace_dir = data.get('dir', './workspace')
    
    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return jsonify({
                "message": "Repository updated successfully",
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git pull failed",
                "stderr": result.stderr
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/list', methods=['GET'])
def list_files():
    """List files in the workspace directory"""
    workspace_dir = request.args.get('dir', './workspace')
    
    try:
        if not os.path.exists(workspace_dir):
            return jsonify({"files": [], "message": "Directory does not exist"})
        
        files = []
        for root, dirs, filenames in os.walk(workspace_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, workspace_dir)
                files.append(rel_path)
        
        return jsonify({
            "files": sorted(files),
            "directory": workspace_dir,
            "count": len(files)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/read', methods=['GET'])
def read_file():
    """Read content of a specific file"""
    file_path = request.args.get('path')
    workspace_dir = request.args.get('dir', './workspace')
    
    if not file_path:
        return jsonify({"error": "Missing 'path' parameter"}), 400
    
    try:
        full_path = os.path.join(workspace_dir, file_path)
        
        # Security check: ensure the file is within workspace
        if not os.path.abspath(full_path).startswith(os.path.abspath(workspace_dir)):
            return jsonify({"error": "Access denied: file outside workspace"}), 403
        
        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "content": content,
            "file_path": file_path,
            "size": len(content)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/write', methods=['POST'])
def write_file():
    """Write content to a specific file"""
    data = request.get_json()
    if not data or 'path' not in data or 'content' not in data:
        return jsonify({"error": "Invalid request. 'path' and 'content' fields are required."}), 400
    
    file_path = data['path']
    content = data['content']
    workspace_dir = data.get('dir', './workspace')
    
    try:
        full_path = os.path.join(workspace_dir, file_path)
        
        # Security check: ensure the file is within workspace
        if not os.path.abspath(full_path).startswith(os.path.abspath(workspace_dir)):
            return jsonify({"error": "Access denied: file outside workspace"}), 403
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "message": "File written successfully",
            "file_path": file_path,
            "size": len(content)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "gemini_available": True})

if __name__ == '__main__':
    # Initialize Gemini CLI on startup
    logging.info("Starting agent service with Gemini CLI support...")
    start_gemini_cli()
    
    # Runs on port 5000 inside the container
    app.run(host='0.0.0.0', port=5000)
