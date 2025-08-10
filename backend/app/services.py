import docker
import traceback
import git
import tempfile
import shutil
from typing import Optional

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Docker is not running or configured correctly: {e}")

    def list_remote_branches(self, repo_url: str, token: Optional[str]) -> list[str]:
        """Lists remote branches without cloning the whole repo."""
        temp_dir = tempfile.mkdtemp()
        try:
            g = git.cmd.Git(temp_dir)
            
            url_no_protocol = repo_url.split('//', 1)[-1]
            if token:
                auth_url = f"https://oauth2:{token}@{url_no_protocol}"
            else:
                auth_url = f"https://{url_no_protocol}"

            # ls-remote is a lightweight way to get refs from a remote repo
            output = g.ls_remote('--heads', auth_url)
            
            # Output format is: <commit_hash>\trefs/heads/<branch_name>
            branches = [line.split('\t')[1].replace('refs/heads/', '') for line in output.splitlines()]
            return sorted(branches)
        finally:
            shutil.rmtree(temp_dir)

    def create_and_run_environment(
        self, container_name: str, base_image: str, git_repo_url: str, 
        env_name: str, env_vars: dict, branch_mode: str, existing_branch: Optional[str]
    ):
        setup_script = f"""
        #!/bin/sh
        set -ex
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y && apt-get install -y curl git
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
        npm install -g @google/gemini-cli --unsafe-perm=true --allow-root
        
        url_no_protocol=$(echo \"{git_repo_url}\" | sed -e 's|^[^:]*://||')
        
        if [ -n "$GIT_TOKEN" ]; then
            clone_url="https://oauth2:$GIT_TOKEN@$url_no_protocol"
        else
            clone_url="https://$url_no_protocol"
        fi
        
git clone "$clone_url" /workspace 2>&1
        cd /workspace
        git config --global user.name "Gemini Agent"
        git config --global user.email "agent@example.com"
        
        # This is the new conditional logic for branch handling
        if [ \"{branch_mode}\" = \"new\" ]; then
            branch_name="feature/{env_name}"
            git checkout -b "$branch_name"
            git push --set-upstream origin "$branch_name"
        else
            git checkout "{existing_branch}"
            # Ensure the local branch tracks the remote branch
            git branch --set-upstream-to=origin/"{existing_branch}" "{existing_branch}"
        fi
        
        touch /tmp/setup_complete
        tail -f /dev/null
        """
        try:
            self.client.containers.run(
                image=base_image,
                name=container_name,
                command=["/bin/sh", "-c", setup_script],
                environment=env_vars,
                detach=True
            )
        except Exception as e:
            traceback.print_exc()
            self.remove_container(container_name)
            raise e

    # ... (other methods remain the same)
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

    def remove_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
        except docker.errors.NotFound: pass

    def setup_shell_session(self, container_name: str):
        container = self.client.containers.get(container_name)
        if container.status != "running":
            raise RuntimeError(f"Container {container_name} is not running.")
        
        robust_start_command = """
        sh -c '
          if [ -f /etc/environment ]; then . /etc/environment; fi
          export TERM=xterm-256color
          while [ ! -f "/tmp/setup_complete" ]; do
            sleep 1
          done
          gemini
        '
        """
        
        exec_instance = self.api_client.exec_create(
            container.id,
            robust_start_command,
            stdin=True,
            tty=True,
            workdir="/workspace"
        )
        exec_id = exec_instance['Id']
        socket = self.api_client.exec_start(exec_id, tty=True, socket=True)
        return exec_id, socket._sock

    def resize_shell(self, exec_id: str, rows: int, cols: int):
        self.api_client.exec_resize(exec_id, height=rows, width=cols)

docker_service = DockerService()
