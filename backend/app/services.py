import json
import docker
import traceback
import git
import tempfile
import shutil
from typing import Optional, List, Dict, Any

# --- Data Persistence Service ---

class ProjectService:
    def __init__(self, db_path: str = 'data/db.json'):
        self.db_path = db_path

    def _load_data(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is empty/corrupted, start fresh
            return {"users": [], "projects": []}

    def _save_data(self, data: Dict[str, List[Dict[str, Any]]]):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    # Project-specific methods
    def get_projects(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        return data.get("projects", [])

    def get_project(self, name: str) -> Optional[Dict[str, Any]]:
        projects = self.get_projects()
        for p in projects:
            if p.get("name") == name:
                return p
        return None

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load_data()
        if self.get_project(project_data["name"]):
            raise ValueError("Project with this name already exists.")
        
        # Ensure the projects list exists
        if "projects" not in data:
            data["projects"] = []
            
        data["projects"].append(project_data)
        self._save_data(data)
        return project_data

    def update_project(self, name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        project_found = False
        for i, p in enumerate(data.get("projects", [])):
            if p.get("name") == name:
                # Update the project dictionary
                data["projects"][i].update(updates)
                project_found = True
                break
        
        if not project_found:
            return None
            
        self._save_data(data)
        return data["projects"][i]

# --- Docker Service ---
# (DockerService class remains unchanged as it doesn't handle project data persistence)

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Docker is not running or configured correctly: {e}")

    def list_remote_branches(self, repo_url: str, token: Optional[str]) -> list[str]:
        """Lists remote branches without cloning the whole repo."""
        import subprocess
        import signal
        
        try:
            url_no_protocol = repo_url.split('//', 1)[-1]
            if token:
                auth_url = f"https://oauth2:{token}@{url_no_protocol}"
            else:
                auth_url = f"https://{url_no_protocol}"

            # Use subprocess with timeout for better performance
            try:
                # Set a 10-second timeout to prevent hanging
                result = subprocess.run(
                    ['git', 'ls-remote', '--heads', auth_url],
                    capture_output=True,
                    text=True,
                    timeout=10,  # 10-second timeout
                    check=True
                )
                output = result.stdout
            except subprocess.TimeoutExpired:
                raise Exception("Request timed out - repository may be slow or unreachable")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to fetch remote branches: {e.stderr or str(e)}")
            except Exception as e:
                raise Exception(f"Failed to fetch remote branches: {str(e)}")
            
            if not output.strip():
                return ['main', 'master']  # Default branches if no output
                
            branches = [line.split('\t')[1].replace('refs/heads/', '') for line in output.splitlines() if '\t' in line]
            return sorted(branches) if branches else ['main', 'master']
            
        except Exception as e:
            # Log the actual error for debugging
            error_msg = f"Could not fetch remote branches: {str(e)}"
            print(f"Error: {error_msg}")
            # Re-raise the exception instead of silently returning default branches
            # This allows the API to return proper error messages to the frontend
            raise Exception(error_msg)

    def create_and_run_environment(
        self, container_name: str, base_image: str, git_repo_url: str, 
        env_name: str, env_vars: dict, branch_mode: str, existing_branch: Optional[str],
        ai_tool: str = "gemini"
    ):
        setup_script = f"""
        #!/bin/sh
        set -ex
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y && apt-get install -y curl git
        
        # Install Node.js for both tools
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
        
        # Install AI tool based on selection
        if [ "{ai_tool}" = "gemini" ]; then
            npm install -g @google/gemini-cli --unsafe-perm=true --allow-root
            agent_name="Gemini Agent"
        else
            npm install -g @anthropic-ai/claude-code --unsafe-perm=true --allow-root
            agent_name="Claude Agent"
        fi
        
        url_no_protocol=$(echo \"{git_repo_url}\" | sed -e 's|^[^:]*://||')
        
        if [ -n "$GIT_TOKEN" ]; then
            clone_url="https://oauth2:$GIT_TOKEN@$url_no_protocol"
        else
            clone_url="https://$url_no_protocol"
        fi
        
git clone "$clone_url" /workspace 2>&1
        cd /workspace
        git config --global user.name "$agent_name"
        git config --global user.email "agent@example.com"
        
        # If using Google login mode for Gemini, create a script to handle login
        if [ "{ai_tool}" = "gemini" ] && [ "$GEMINI_USE_GOOGLE_LOGIN" = "true" ]; then
            cat > /workspace/gemini-login.sh << 'EOF'
#!/bin/bash
echo "Google Login Mode: Run 'gemini login' to authenticate with your Google account"
EOF
            chmod +x /workspace/gemini-login.sh
        fi
        
        if [ \"{branch_mode}\" = \"new\" ]; then
            branch_name="feature/{env_name}"
            git checkout -b "$branch_name"
            git push --set-upstream origin "$branch_name"
        else
            # For existing branch, fetch all branches first and then checkout
            git fetch origin
            # Try to checkout the branch, creating local branch if it doesn't exist
            git checkout -B "{existing_branch}" origin/"{existing_branch}"
        fi
        
        touch /tmp/setup_complete
        tail -f /dev/null
        """
        try:
            # Prepare volumes for Claude session persistence
            volumes = {}
            if ai_tool == "claude":
                # Create directory for Claude sessions if it doesn't exist
                import os
                claude_session_dir = f"data/claude_sessions/{container_name}"
                os.makedirs(claude_session_dir, exist_ok=True)
                volumes[os.path.abspath(claude_session_dir)] = {
                    'bind': '/root/.claude/projects/-workspace',
                    'mode': 'rw'
                }
            
            self.client.containers.run(
                image=base_image,
                name=container_name,
                command=["/bin/sh", "-c", setup_script],
                environment=env_vars,
                volumes=volumes,
                detach=True
            )
        except Exception as e:
            traceback.print_exc()
            self.remove_container(container_name)
            raise e

    def list_images(self) -> list[str]:
        images = self.client.images.list()
        tags = [tag for image in images if image.tags for tag in image.tags]
        return sorted(tags)

    def stop_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            if container.status == "running":
                container.stop()
        except docker.errors.NotFound: pass

    def start_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            if container.status != "running":
                container.start()
        except docker.errors.NotFound:
            raise ValueError(f"Container {container_name} not found and cannot be started.")

    def remove_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
        except docker.errors.NotFound: pass

    def setup_shell_session(self, container_name: str, ai_tool: str = "gemini"):
        import time
        start_time = time.time()
        print(f"[PERF] setup_shell_session started for {container_name} with {ai_tool}")
        
        container = self.client.containers.get(container_name)
        if container.status != "running":
            raise RuntimeError(f"Container {container_name} is not running.")
        
        setup_check_start = time.time()
        # Check if the setup is complete by checking for the setup_complete file
        try:
            result = container.exec_run("test -f /tmp/setup_complete")
            if result.exit_code != 0:
                raise RuntimeError("Environment is still initializing. Please wait for setup to complete.")
        except:
            raise RuntimeError("Environment is still initializing. Please wait for setup to complete.")
        
        setup_check_time = time.time() - setup_check_start
        print(f"[PERF] Setup check took {setup_check_time:.3f}s")
        
        ai_command = "claude" if ai_tool == "claude" else "gemini"
        
        # For Gemini with Google login, we need to handle the login process differently
        if ai_tool == "gemini":
            # Build command using a list to avoid quoting issues
            cmd = [
                "sh", "-c",
                "if [ -f /etc/environment ]; then . /etc/environment; fi; "
                "export TERM=xterm-256color; "
                "while [ ! -f \"/tmp/setup_complete\" ]; do "
                "  sleep 1; "
                "done; "
                "if [ \"$GEMINI_USE_GOOGLE_LOGIN\" = \"true\" ]; then "
                "  echo \"Google Login Mode: Run 'gemini login' to authenticate with your Google account\"; "
                "  echo \"After login, run 'gemini' to start the CLI\"; "
                "  exec /bin/bash; "
                "else "
                "  exec gemini; "
                "fi"
            ]
        else:
            # Claude with simple session continuation
            print(f"[PERF] Using claude -c for session continuation")
            cmd = [
                "sh", "-c",
                "echo \"[PERF] Starting Claude session recovery at $(date)\"; "
                "if [ -f /etc/environment ]; then . /etc/environment; fi; "
                "export TERM=xterm-256color; "
                "while [ ! -f \"/tmp/setup_complete\" ]; do "
                "  sleep 1; "
                "done; "
                "echo \"[PERF] Setup complete check passed at $(date)\"; "
                "cd /workspace; "
                "echo \"[PERF] Changed to workspace directory at $(date)\"; "
                "echo \"[PERF] Attempting to continue previous session at $(date)\"; "
                "echo \"[DEBUG] Checking claude command availability...\"; "
                "which claude || echo \"[ERROR] claude command not found\"; "
                "echo \"[DEBUG] Current directory: $(pwd)\"; "
                "echo \"[DEBUG] Environment variables:\"; "
                "env | grep -E '(ANTHROPIC|CLAUDE)' || echo \"[DEBUG] No ANTHROPIC/CLAUDE env vars found\"; "
                "echo \"[DEBUG] Running claude -c with proper TTY setup...\"; "
                "echo \"[DEBUG] Checking for existing sessions...\"; "
                "ls -la ~/.claude/ 2>/dev/null || echo \"[DEBUG] No ~/.claude directory found\"; "
                "echo \"[DEBUG] Attempting session continuation...\"; "
                "script -qec 'claude -c' /dev/null 2>&1 || { "
                "  echo \"[DEBUG] Session continuation failed, trying direct claude start...\"; "
                "  script -qec 'claude' /dev/null 2>&1 || { "
                "    echo \"[ERROR] Both session continuation and new session failed\"; "
                "    echo \"[FALLBACK] Starting basic claude without TTY...\"; "
                "  }; "
                "};"
            ]
        
        cmd_creation_start = time.time()
        exec_instance = self.api_client.exec_create(
            container.id,
            cmd,
            stdin=True,
            tty=True,
            workdir="/workspace"
        )
        cmd_creation_time = time.time() - cmd_creation_start
        print(f"[PERF] Command creation took {cmd_creation_time:.3f}s")
        
        exec_id = exec_instance['Id']
        
        socket_start_time = time.time()
        socket = self.api_client.exec_start(exec_id, tty=True, socket=True)
        socket_start_time_elapsed = time.time() - socket_start_time
        print(f"[PERF] Socket start took {socket_start_time_elapsed:.3f}s")
        
        total_time = time.time() - start_time
        print(f"[PERF] Total setup_shell_session took {total_time:.3f}s")
        
        return exec_id, socket._sock

    def resize_shell(self, exec_id: str, rows: int, cols: int):
        self.api_client.exec_resize(exec_id, height=rows, width=cols)

# Instantiate services
project_service = ProjectService()
docker_service = DockerService()