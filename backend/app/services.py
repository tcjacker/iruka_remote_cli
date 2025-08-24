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

    def update_environment_status(self, project_name: str, env_id: str, updates: Dict[str, Any]):
        """Updates a specific environment within a project."""
        data = self._load_data()
        projects = data.get("projects", [])
        for proj in projects:
            if proj.get("name") == project_name:
                environments = proj.get("environments", [])
                for env in environments:
                    if env.get("id") == env_id:
                        env.update(updates)
                        self._save_data(data)
                        return True
        return False

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
        import re
        import logging
        
        logger = logging.getLogger("uvicorn")
        logger.info(f"[Git Service] 开始获取远程分支，仓库URL: {repo_url}")
        
        try:
            # Clean the URL - remove any invisible characters and trailing/leading whitespace
            original_url = repo_url
            repo_url = repo_url.strip()
            
            if original_url != repo_url:
                logger.info(f"[Git Service] URL已清理空白字符，原始长度: {len(original_url)}, 清理后长度: {len(repo_url)}")
            
            # Extract the protocol and domain parts correctly
            if '//' in repo_url:
                url_no_protocol = repo_url.split('//', 1)[-1]
                logger.info(f"[Git Service] 从URL中提取域名部分: {url_no_protocol}")
            else:
                # If no protocol specified, assume https
                url_no_protocol = repo_url
                logger.info(f"[Git Service] URL没有协议前缀，使用原始值: {url_no_protocol}")
                
            # Remove any trailing invisible characters that might cause issues
            original_no_protocol = url_no_protocol
            url_no_protocol = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F]', '', url_no_protocol)
            
            if original_no_protocol != url_no_protocol:
                logger.info(f"[Git Service] 已移除不可见Unicode字符，原始长度: {len(original_no_protocol)}, 清理后长度: {len(url_no_protocol)}")
                # 输出十六进制表示以便调试
                logger.info(f"[Git Service] 原始URL十六进制: {original_no_protocol.encode('utf-8').hex()}")
                logger.info(f"[Git Service] 清理后URL十六进制: {url_no_protocol.encode('utf-8').hex()}")
            
            if token:
                # 隐藏令牌的大部分内容，只显示前4位和后4位
                masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
                logger.info(f"[Git Service] 使用令牌构建认证URL，令牌(部分隐藏): {masked_token}")
                auth_url = f"https://oauth2:{token}@{url_no_protocol}"
            else:
                logger.info(f"[Git Service] 未提供令牌，使用普通HTTPS URL")
                auth_url = f"https://{url_no_protocol}"

            # Use subprocess with timeout for better performance
            try:
                # 记录即将执行的Git命令（隐藏认证信息）
                safe_url = auth_url.replace(token, "***") if token else auth_url
                logger.info(f"[Git Service] 执行命令: git ls-remote --heads {safe_url}")
                logger.info(f"[Git Service] 设置超时时间: 10秒")
                
                # 记录开始时间
                import time
                start_time = time.time()
                
                # Set a 10-second timeout to prevent hanging
                result = subprocess.run(
                    ['git', 'ls-remote', '--heads', auth_url],
                    capture_output=True,
                    text=True,
                    timeout=10,  # 10-second timeout
                    check=True
                )
                
                # 计算执行时间
                execution_time = time.time() - start_time
                logger.info(f"[Git Service] 命令执行完成，耗时: {execution_time:.2f}秒")
                
                output = result.stdout
                output_lines = output.strip().split('\n') if output.strip() else []
                logger.info(f"[Git Service] 命令输出行数: {len(output_lines)}")
                
            except subprocess.TimeoutExpired:
                logger.error(f"[Git Service] 命令执行超时 (>10秒)")
                raise Exception("Request timed out - repository may be slow or unreachable")
            except subprocess.CalledProcessError as e:
                logger.error(f"[Git Service] 命令执行失败: {e.stderr or str(e)}")
                raise Exception(f"Failed to fetch remote branches: {e.stderr or str(e)}")
            except Exception as e:
                logger.error(f"[Git Service] 发生异常: {str(e)}")
                raise Exception(f"Failed to fetch remote branches: {str(e)}")
                
            logger.info(f"[Git Service] 命令执行成功，开始解析分支信息")
            
            if not output.strip():
                logger.warning(f"[Git Service] 命令输出为空，返回默认分支 ['main', 'master']")
                return ['main', 'master']  # Default branches if no output
            
            # 输出前10行作为调试信息（如果有）
            preview_lines = output.splitlines()[:10]
            logger.info(f"[Git Service] 命令输出前{len(preview_lines)}行:\n" + "\n".join(preview_lines))
                
            branches = [line.split('\t')[1].replace('refs/heads/', '') for line in output.splitlines() if '\t' in line]
            
            if not branches:
                logger.warning(f"[Git Service] 无法从输出中解析分支，返回默认分支 ['main', 'master']")
                return ['main', 'master']
            
            sorted_branches = sorted(branches)
            logger.info(f"[Git Service] 成功解析到{len(sorted_branches)}个分支: {', '.join(sorted_branches[:5])}{', ...' if len(sorted_branches) > 5 else ''}")
            return sorted_branches
            
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
        except docker.errors.NotFound:
            print(f"Container {container_name} not found, skipping stop.")
        except Exception as e:
            print(f"Error stopping container {container_name}: {e}")

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
        except docker.errors.NotFound:
            print(f"Container {container_name} not found, skipping remove.")
        except Exception as e:
            print(f"Error removing container {container_name}: {e}")

    def stop_and_remove_container(self, container_name: str):
        self.stop_container(container_name)
        self.remove_container(container_name)

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
        
        return exec_id, socket

    def resize_shell(self, exec_id: str, rows: int, cols: int):
        self.api_client.exec_resize(exec_id, height=rows, width=cols)

# Instantiate services
project_service = ProjectService()
docker_service = DockerService()