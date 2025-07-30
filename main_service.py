import docker
from docker.api import APIClient
import uuid
import requests
import time
from flask import Flask, request, jsonify
import logging
import os
import json

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
AGENT_IMAGE_TAG = 'agent-service:latest'
AGENT_INTERNAL_PORT = '5000'
MAIN_SERVICE_PORT = 8081

# --- Flask App and Docker Client Initialization ---
app = Flask(__name__)
try:
    # Use the low-level APIClient with the verified socket path.
    client = APIClient(base_url='unix:///Users/tc/.docker/run/docker.sock', user_agent='Docker-Py-Stable')
    # Verify the connection
    client.ping()
    logging.info("Successfully connected to Docker using APIClient.")
except Exception as e:
    logging.error(f"CRITICAL: Failed to connect to Docker. Please ensure Docker is running. Error: {e}")
    exit(1)

# --- In-memory storage for environment details ---
environments = {}


@app.route('/environments', methods=['POST'])
def create_environment():
    """Creates a new agent environment using the low-level APIClient."""
    env_id = str(uuid.uuid4())

    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            host_port = s.getsockname()[1]

        logging.info(f"Creating container for new environment {env_id} on host port {host_port}...")

        host_config = client.create_host_config(
            port_bindings={AGENT_INTERNAL_PORT: host_port}
        )

        container = client.create_container(
            image=AGENT_IMAGE_TAG,
            ports=[AGENT_INTERNAL_PORT],
            host_config=host_config
        )

        client.start(container=container['Id'])

        environments[env_id] = {
            "container_id": container['Id'],
            "port": host_port,
            "status": "running"
        }

        logging.info(f"Environment {env_id} created successfully with container ID {container['Id']}.")
        return jsonify({
            "message": "Environment created successfully.",
            "env_id": env_id,
            "port": host_port
        }), 201

    except Exception as e:
        logging.error(f"Failed to create environment: {e}")
        # Check for the specific "No such image" error to give a helpful message.
        if 'No such image' in str(e):
            logging.error("The agent-service:latest image was not found.")
            logging.error("Please build it manually by running: docker build -t agent-service:latest ./agent")
            return jsonify(
                {"error": "Failed to create environment: Agent image not found. Please build it first."}), 500
        return jsonify({"error": f"Failed to create environment: {str(e)}"}), 500


@app.route('/environments/<string:env_id>/execute', methods=['POST'])
def execute_in_environment(env_id):
    """Executes a command within a specified agent environment."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    port = env_details['port']

    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "Invalid request. 'command' field is required."}), 400

    command = data['command']
    logging.info(f"Executing command in env {env_id} on port {port}: {command}")

    try:
        agent_url = f"http://127.0.0.1:{port}/execute"
        response = requests.post(agent_url, json={"command": command}, timeout=60)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code

    except requests.exceptions.Timeout:
        logging.error(f"Request to agent in env {env_id} timed out.")
        return jsonify({"error": "Agent execution timed out."}), 504
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to communicate with agent in env {env_id}: {e}")
        return jsonify({"error": f"Failed to communicate with agent: {str(e)}"}), 502


@app.route('/environments/<string:env_id>/gemini', methods=['POST'])
def gemini_chat_in_environment(env_id):
    """Send a prompt to Gemini CLI within a specified agent environment."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    port = env_details['port']

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Invalid request. 'prompt' field is required."}), 400

    prompt = data['prompt']
    api_key = data.get('api_key')  # Optional API key
    logging.info(f"Sending Gemini prompt in env {env_id} on port {port}: {prompt[:100]}...")

    try:
        agent_url = f"http://127.0.0.1:{port}/gemini"
        payload = {"prompt": prompt}
        if api_key:
            payload["api_key"] = api_key
        response = requests.post(agent_url, json=payload, timeout=120)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code

    except requests.exceptions.Timeout:
        logging.error(f"Gemini request to agent in env {env_id} timed out.")
        return jsonify({"error": "Gemini request timed out."}), 504
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to communicate with Gemini in env {env_id}: {e}")
        return jsonify({"error": f"Failed to communicate with Gemini: {str(e)}"}), 502


@app.route('/environments/<string:env_id>/gemini/status', methods=['GET'])
def gemini_status_in_environment(env_id):
    """Check Gemini CLI status within a specified agent environment."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    port = env_details['port']

    try:
        agent_url = f"http://127.0.0.1:{port}/gemini/status"
        response = requests.get(agent_url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to check Gemini status in env {env_id}: {e}")
        return jsonify({"error": f"Failed to check Gemini status: {str(e)}"}), 502


@app.route('/environments/<string:env_id>/gemini/restart', methods=['POST'])
def restart_gemini_in_environment(env_id):
    """Restart Gemini CLI within a specified agent environment."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    port = env_details['port']

    try:
        agent_url = f"http://127.0.0.1:{port}/gemini/restart"
        response = requests.post(agent_url, timeout=30)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to restart Gemini in env {env_id}: {e}")
        return jsonify({"error": f"Failed to restart Gemini: {str(e)}"}), 502


@app.route('/environments/<string:env_id>/gemini/configure', methods=['POST'])
def configure_gemini_in_environment(env_id):
    """Configure Gemini API key within a specified agent environment."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    port = env_details['port']

    data = request.get_json()
    if not data or 'api_key' not in data:
        return jsonify({"error": "Invalid request. 'api_key' field is required."}), 400

    api_key = data['api_key']
    logging.info(f"Configuring Gemini API key in env {env_id} on port {port}")

    try:
        agent_url = f"http://127.0.0.1:{port}/gemini/configure"
        response = requests.post(agent_url, json={"api_key": api_key}, timeout=30)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to configure Gemini API key in env {env_id}: {e}")
        return jsonify({"error": f"Failed to configure API key: {str(e)}"}), 502


@app.route('/environments/<string:env_id>', methods=['DELETE'])
def delete_environment(env_id):
    """Stops and removes the container using the low-level APIClient."""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    env_details = environments[env_id]
    container_id = env_details['container_id']
    logging.info(f"Deleting environment {env_id} (Container ID: {container_id})...")

    try:
        logging.info(f"Stopping container {container_id}...")
        client.stop(container=container_id)
        logging.info(f"Removing container {container_id}...")
        client.remove_container(container=container_id)

        del environments[env_id]

        logging.info(f"Environment {env_id} deleted successfully.")
        return jsonify({"message": f"Environment {env_id} deleted successfully."}), 200

    except docker.errors.NotFound:
        logging.warning(f"Container {container_id} for env {env_id} not found.")
        del environments[env_id]
        return jsonify({"message": "Container not found, environment record cleaned up."}), 200
    except Exception as e:
        logging.error(f"Failed to delete environment {env_id}: {e}")
        return jsonify({"error": f"Failed to delete environment: {str(e)}"}), 500


# ==================== Git Integration Endpoints ====================

@app.route('/environments/<string:env_id>/git/clone', methods=['POST'])
def git_clone(env_id):
    """Clone a Git repository in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json()

    try:
        agent_url = f"http://127.0.0.1:{port}/git/clone"
        response = requests.post(agent_url, json=data, timeout=60)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to clone repository in env {env_id}: {e}")
        return jsonify({"error": f"Failed to clone repository: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/git/status', methods=['GET'])
def git_status(env_id):
    """Get Git status in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    workspace_dir = request.args.get('dir', './workspace')

    try:
        agent_url = f"http://127.0.0.1:{port}/git/status"
        response = requests.get(agent_url, params={'dir': workspace_dir}, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get git status in env {env_id}: {e}")
        return jsonify({"error": f"Failed to get git status: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/git/add', methods=['POST'])
def git_add(env_id):
    """Add files to Git staging area in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json()

    try:
        agent_url = f"http://127.0.0.1:{port}/git/add"
        response = requests.post(agent_url, json=data, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to add files to git in env {env_id}: {e}")
        return jsonify({"error": f"Failed to add files: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/git/commit', methods=['POST'])
def git_commit(env_id):
    """Commit changes in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json()

    try:
        agent_url = f"http://127.0.0.1:{port}/git/commit"
        response = requests.post(agent_url, json=data, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to commit changes in env {env_id}: {e}")
        return jsonify({"error": f"Failed to commit changes: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/git/push', methods=['POST'])
def git_push(env_id):
    """Push changes to remote repository in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json() or {}

    try:
        agent_url = f"http://127.0.0.1:{port}/git/push"
        response = requests.post(agent_url, json=data, timeout=60)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to push changes in env {env_id}: {e}")
        return jsonify({"error": f"Failed to push changes: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/git/pull', methods=['POST'])
def git_pull(env_id):
    """Pull latest changes from remote repository in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json() or {}

    try:
        agent_url = f"http://127.0.0.1:{port}/git/pull"
        response = requests.post(agent_url, json=data, timeout=60)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to pull changes in env {env_id}: {e}")
        return jsonify({"error": f"Failed to pull changes: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/files/list', methods=['GET'])
def list_files(env_id):
    """List files in the workspace of the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    workspace_dir = request.args.get('dir', './workspace')

    try:
        agent_url = f"http://127.0.0.1:{port}/files/list"
        response = requests.get(agent_url, params={'dir': workspace_dir}, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to list files in env {env_id}: {e}")
        return jsonify({"error": f"Failed to list files: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/files/read', methods=['GET'])
def read_file(env_id):
    """Read a file from the workspace of the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    file_path = request.args.get('path')
    workspace_dir = request.args.get('dir', './workspace')

    if not file_path:
        return jsonify({"error": "Missing 'path' parameter"}), 400

    try:
        agent_url = f"http://127.0.0.1:{port}/files/read"
        response = requests.get(agent_url, params={'path': file_path, 'dir': workspace_dir}, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to read file in env {env_id}: {e}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/files/write', methods=['POST'])
def write_file(env_id):
    """Write content to a file in the workspace of the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json()

    try:
        agent_url = f"http://127.0.0.1:{port}/files/write"
        response = requests.post(agent_url, json=data, timeout=30)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to write file in env {env_id}: {e}")
        return jsonify({"error": f"Failed to write file: {str(e)}"}), 502

@app.route('/environments/<string:env_id>/execute', methods=['POST'])
def execute_command(env_id):
    """Execute a shell command in the specified environment"""
    if env_id not in environments:
        return jsonify({"error": "Environment not found."}), 404

    port = environments[env_id]['port']
    data = request.get_json()

    try:
        agent_url = f"http://127.0.0.1:{port}/execute"
        response = requests.post(agent_url, json=data, timeout=60)
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to execute command in env {env_id}: {e}")
        return jsonify({"error": f"Failed to execute command: {str(e)}"}), 502


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for main service"""
    return jsonify({"status": "healthy", "service": "main_service"})

if __name__ == '__main__':
    logging.info("Starting main service. Please ensure 'agent-service:latest' image is built.")
    app.run(host='0.0.0.0', port=MAIN_SERVICE_PORT)
