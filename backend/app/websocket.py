import asyncio
import json
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .services import docker_service
from urllib.parse import unquote

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
    # Accept the connection first to be able to send error messages
    await websocket.accept()
    
    # Get the token from the query parameters
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_text("[Authentication Error] No token provided.\r\n")
        await websocket.close()
        return
    
    # Validate the token
    from .auth import verify_token
    try:
        user = verify_token(token)
        print(f"WebSocket authentication successful for user: {user.username}")
    except Exception as e:
        print(f"Authentication error: {e}")
        await websocket.send_text("[Authentication Error] Invalid token.\r\n")
        await websocket.close()
        return
    
    # URL decode the project name in case it contains UTF-8 encoded characters
    decoded_project_name = unquote(project_name)
    
    # First check if the environment is still initializing
    from .services import project_service
    proj = project_service.get_project(decoded_project_name)
    if proj:
        env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
        if env and env.get("status") == "pending":
            await websocket.send_text("[Environment Initializing] Please wait while the environment is being set up...\r\n")
            # We could wait for the setup to complete, but for now let's just inform the user
    
    # Sanitize names to construct the correct container name
    sane_project_name = sanitize_for_docker(decoded_project_name)
    sane_env_id = sanitize_for_docker(env_id)
    
    # Try to determine if this is a Claude or Gemini environment by checking the project data
    ai_tool = "gemini"  # default
    container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
    
    if proj:
        env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
        if env and env.get("ai_tool") == "claude":
            ai_tool = "claude"
            container_name = f"claude-env-{sane_project_name}-{sane_env_id}"
    
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