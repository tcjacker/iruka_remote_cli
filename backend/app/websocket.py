import asyncio
import json
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .services import docker_service

router = APIRouter()

# --- Helper Functions (copied from api.py for consistency) ---
def sanitize_for_docker(name: str) -> str:
    """Sanitizes a string to be a valid Docker container name."""
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '', name)
    if sanitized.startswith(('_', '.', '-')):
        sanitized = 'container' + sanitized
    return sanitized

@router.websocket("/ws/shell/{project_name}/{env_id}")
async def websocket_shell(websocket: WebSocket, project_name: str, env_id: str):
    await websocket.accept()
    
    # First check if the environment is still initializing
    from .services import project_service
    proj = project_service.get_project(project_name)
    if proj:
        env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
        if env and env.get("status") == "pending":
            await websocket.send_text("[Environment Initializing] Please wait while the environment is being set up...\r\n")
            # We could wait for the setup to complete, but for now let's just inform the user
    
    # Sanitize names to construct the correct container name
    sane_project_name = sanitize_for_docker(project_name)
    sane_env_id = sanitize_for_docker(env_id)
    
    # Try to determine if this is a Claude or Gemini environment
    claude_container_name = f"claude-env-{sane_project_name}-{sane_env_id}"
    gemini_container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
    
    # Check which container exists
    from .services import docker_service
    try:
        docker_service.client.containers.get(claude_container_name)
        container_name = claude_container_name
        ai_tool = "claude"
    except:
        container_name = gemini_container_name
        ai_tool = "gemini"
    
    exec_id = None
    shell_socket = None
    
    try:
        exec_id, shell_socket = docker_service.setup_shell_session(container_name, ai_tool)
        
        async def forward_client_to_shell():
            """Reads from the client and sends to the shell."""
            while True:
                try:
                    raw_data = await websocket.receive_text()
                    msg = json.loads(raw_data)
                    
                    if msg.get('type') == 'input':
                        shell_socket.sendall(msg['data'].encode('utf-8'))
                    elif msg.get('type') == 'resize':
                        docker_service.resize_shell(exec_id, msg['rows'], msg['cols'])
                except WebSocketDisconnect:
                    break
                except Exception:
                    break

        async def forward_shell_to_client():
            """Reads from the shell and sends to the client."""
            loop = asyncio.get_running_loop()
            while True:
                try:
                    output = await loop.run_in_executor(
                        None, shell_socket.recv, 4096
                    )
                    if output:
                        await websocket.send_text(output.decode('utf-8', errors='ignore'))
                    else:
                        break
                except Exception:
                    break

        await asyncio.gather(forward_client_to_shell(), forward_shell_to_client())

    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
    finally:
        if shell_socket:
            shell_socket.close()
        print(f"Connection handler for {container_name} finished.")