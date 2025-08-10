import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .services import docker_service

router = APIRouter()

@router.websocket("/ws/shell/{project_name}/{env_id}")
async def websocket_shell(websocket: WebSocket, project_name: str, env_id: str):
    await websocket.accept()
    container_name = f"gemini-env-{project_name}-{env_id}"
    exec_id = None
    shell_socket = None
    
    try:
        exec_id, shell_socket = docker_service.setup_shell_session(container_name)
        
        # This is the simplest possible loop to forward data.
        # It directly bridges the client WebSocket and the Docker exec socket.
        
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
                    # Use run_in_executor to avoid blocking the main thread
                    output = await loop.run_in_executor(
                        None, shell_socket.recv, 4096
                    )
                    if output:
                        await websocket.send_text(output.decode('utf-8', errors='ignore'))
                    else:
                        # Socket closed
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
