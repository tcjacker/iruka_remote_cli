import asyncio
import json
import re
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .services import docker_service
from urllib.parse import unquote

router = APIRouter()

# WebSocket configuration
WEBSOCKET_TIMEOUT = 300  # 5 minutes timeout
HEARTBEAT_INTERVAL = 30  # Send heartbeat every 30 seconds
MAX_IDLE_TIME = 600  # 10 minutes max idle time before disconnect

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
    
    print(f"WebSocket connection attempt - project_name: '{project_name}', env_id: '{env_id}'")
    
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
    try:
        decoded_project_name = unquote(project_name)
        print(f"Decoded project name: '{decoded_project_name}'")
    except Exception as e:
        print(f"Error decoding project name: {e}")
        await websocket.send_text("[Error] Invalid project name encoding.\r\n")
        await websocket.close()
        return
        
    # On successful connection, clear the disconnected_at timestamp
    from .services import project_service
    project_service.update_environment_status(
        decoded_project_name, env_id, {"disconnected_at": None}
    )
    print(f"Cleared disconnected_at timestamp for env {env_id}")
    
    # First check if the environment is still initializing
    proj = project_service.get_project(decoded_project_name)
    if proj:
        env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
        if env and env.get("status") == "pending":
            await websocket.send_text("[Environment Initializing] Please wait while the environment is being set up...\r\n")
            # We could wait for the setup to complete, but for now let's just inform the user
    
    # Sanitize names to construct the correct container name
    print(f"Sanitizing project name: '{decoded_project_name}' and env_id: '{env_id}'")
    sane_project_name = sanitize_for_docker(decoded_project_name)
    sane_env_id = sanitize_for_docker(env_id)
    print(f"Sanitized names - project: '{sane_project_name}', env: '{sane_env_id}'")
    
    # Try to determine if this is a Claude or Gemini environment by checking the project data
    ai_tool = "gemini"  # default
    container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
    print(f"Initial container name: '{container_name}'")
    
    if proj:
        env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
        if env and env.get("ai_tool") == "claude":
            ai_tool = "claude"
            container_name = f"claude-env-{sane_project_name}-{sane_env_id}"
            print(f"Updated container name for Claude: '{container_name}'")
        else:
            print(f"Using Gemini environment, env ai_tool: {env.get('ai_tool') if env else 'None'}")
    else:
        print("Project not found in database")
    
    exec_id = None
    shell_socket = None
    
    try:
        import time
        websocket_setup_start = time.time()
        print(f"[PERF] WebSocket attempting to set up shell session for container: '{container_name}' with AI tool: '{ai_tool}'")
        exec_id, shell_socket = docker_service.setup_shell_session(container_name, ai_tool)
        websocket_setup_time = time.time() - websocket_setup_start
        print(f"[PERF] WebSocket shell session set up successfully in {websocket_setup_time:.3f}s. exec_id: {exec_id}")
        
        # Use a mutable type (dict) to share the last activity time between tasks
        last_activity = {'time': time.time()}

        async def forward_client_to_shell():
            """Reads from the client, sends to the shell, and manages connection timeout."""
            while True:
                try:
                    # Wait for a message from the client with a timeout
                    raw_data = await asyncio.wait_for(
                        websocket.receive_text(), 
                        timeout=WEBSOCKET_TIMEOUT
                    )
                    msg = json.loads(raw_data)
                    
                    # Any input from the client resets the activity timer
                    last_activity['time'] = time.time()
                    
                    if msg.get('type') == 'input':
                        input_data = msg['data']
                        # Handle /clear command
                        if input_data.strip() == '/clear':
                            await websocket.send_text(json.dumps({
                                'type': 'output',
                                'data': '\033[2J\033[H'
                            }))
                            # Clear sessionId cache for Claude
                            try:
                                from .services import project_service
                                proj = project_service.get_project(decoded_project_name)
                                if proj:
                                    env = next((e for e in proj.get("environments", []) if e["id"] == env_id), None)
                                    if env:
                                        env["sessionId"] = None
                                        project_service.update_project(decoded_project_name, proj)
                                        print(f"Cleared sessionId cache for environment {env_id}")
                            except Exception as e:
                                print(f"Failed to clear sessionId cache: {e}")
                            continue
                        
                        # Forward normal input to shell
                        try:
                            if hasattr(shell_socket, 'sendall'):
                                shell_socket.sendall(input_data.encode('utf-8'))
                            elif hasattr(shell_socket, '_sock'):
                                shell_socket._sock.sendall(input_data.encode('utf-8'))
                            else:
                                shell_socket.send(input_data.encode('utf-8'))
                        except Exception as send_error:
                            print(f"Error sending data to shell: {send_error}")
                            break
                    elif msg.get('type') == 'resize':
                        docker_service.resize_shell(exec_id, msg['rows'], msg['cols'])
                    elif msg.get('type') == 'ping':
                        await websocket.send_text(json.dumps({'type': 'pong', 'timestamp': time.time()}))

                except asyncio.TimeoutError:
                    # This timeout triggers if the client hasn't sent any message.
                    # Now, we check the *shared* last activity time.
                    if time.time() - last_activity['time'] > MAX_IDLE_TIME:
                        print(f"WebSocket idle timeout after {MAX_IDLE_TIME} seconds of no activity (input or output).")
                        break
                    
                    # If the connection is not idle, send a heartbeat to keep it alive
                    try:
                        await websocket.send_text(json.dumps({'type': 'heartbeat', 'timestamp': time.time()}))
                    except Exception:
                        print("Failed to send heartbeat, connection likely dead.")
                        break
                except WebSocketDisconnect:
                    print("WebSocket disconnected by client.")
                    break
                except Exception as e:
                    print(f"Error in forward_client_to_shell: {e}")
                    break

        async def forward_shell_to_client():
            """Reads from the shell and sends to the client."""
            loop = asyncio.get_running_loop()
            while True:
                try:
                    def read_from_socket():
                        try:
                            if hasattr(shell_socket, 'recv'):
                                return shell_socket.recv(4096)
                            elif hasattr(shell_socket, '_sock'):
                                return shell_socket._sock.recv(4096)
                            else:
                                return shell_socket.read(4096)
                        except (socket.timeout, BlockingIOError):
                            return None # Non-blocking, so it's okay to get nothing
                        except Exception as recv_error:
                            print(f"Error reading from shell socket: {recv_error}")
                            return None
                    
                    output = await asyncio.wait_for(
                        loop.run_in_executor(None, read_from_socket),
                        timeout=WEBSOCKET_TIMEOUT
                    )

                    if output:
                        # Any output from the shell resets the activity timer
                        last_activity['time'] = time.time()
                        await websocket.send_text(output.decode('utf-8', errors='ignore'))
                    else:
                        # If read_from_socket returns None because of an error or clean close
                        is_socket_closed = not hasattr(shell_socket, 'fileno') or shell_socket.fileno() == -1
                        if is_socket_closed:
                             print("No more output from shell, socket is closed.")
                             break
                except asyncio.TimeoutError:
                    # This is normal if the shell has no output. Continue waiting.
                    continue
                except Exception as e:
                    print(f"Error in forward_shell_to_client: {e}")
                    break

        print("Starting to gather WebSocket communication tasks")
        await asyncio.gather(forward_client_to_shell(), forward_shell_to_client())

    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_text(f"[Error] {str(e)}\r\n")
    finally:
        # Set the disconnected_at timestamp when the client disconnects
        from .services import project_service
        project_service.update_environment_status(
            decoded_project_name, env_id, {"disconnected_at": time.time()}
        )
        print(f"Set disconnected_at timestamp for env {env_id}")
        
        if shell_socket:
            try:
                shell_socket.close()
                print("Shell socket closed")
            except Exception as e:
                print(f"Error closing shell socket: {e}")
        print(f"Connection handler for {container_name} finished.")