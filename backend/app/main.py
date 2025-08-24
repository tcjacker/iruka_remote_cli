from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .api import auth_router, api_router
from . import websocket
import asyncio
import time
from .services import project_service, docker_service

app = FastAPI()

# --- Background Task for Cleanup ---
async def cleanup_inactive_environments():
    """Periodically checks for inactive environments and stops them."""
    while True:
        print("Running cleanup task for inactive environments...")
        try:
            projects = project_service.get_projects()
            for project in projects:
                environments = project.get("environments", [])
                for env in environments:
                    if env.get("status") == "running" and env.get("disconnected_at"):
                        inactive_time = time.time() - env["disconnected_at"]
                        if inactive_time > 300:  # 5 minutes
                            print(f"Environment {env['id']} in project {project['name']} has been inactive for {inactive_time:.0f}s. Stopping container.")
                            
                            # Determine container name based on AI tool
                            ai_tool = env.get("ai_tool", "gemini")
                            sane_project_name = websocket.sanitize_for_docker(project['name'])
                            sane_env_id = websocket.sanitize_for_docker(env['id'])
                            
                            if ai_tool == "claude":
                                container_name = f"claude-env-{sane_project_name}-{sane_env_id}"
                            else:
                                container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
                            
                            try:
                                docker_service.stop_container(container_name)
                                project_service.update_environment_status(
                                    project['name'], 
                                    env['id'], 
                                    {"status": "stopped", "disconnected_at": None}
                                )
                                print(f"Successfully stopped container {container_name} and updated status.")
                            except Exception as e:
                                print(f"Error stopping container {container_name}: {e}")
        except Exception as e:
            print(f"Error in cleanup task: {e}")
        
        await asyncio.sleep(60)  # Check every 60 seconds

@app.on_event("startup")
async def startup_event():
    """Create a background task for cleanup on startup."""
    asyncio.create_task(cleanup_inactive_environments())

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unprotected auth routes
app.include_router(auth_router, prefix="/api") 
# All other API routes are protected
app.include_router(api_router, prefix="/api") 
# WebSocket router
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "Gemini Docker Manager Backend is running"}
