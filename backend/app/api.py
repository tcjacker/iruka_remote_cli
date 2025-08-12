import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional

from .services import docker_service, project_service
from . import auth
from .auth import User, UserCreate, Token, get_current_user

# Create two routers: one for auth and one for protected API endpoints
auth_router = APIRouter()
api_router = APIRouter()

# --- Helper Functions ---
def sanitize_for_docker(name: str) -> str:
    """Sanitizes a string to be a valid Docker container name."""
    # Remove any characters not allowed by Docker
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '', name)
    # Ensure it doesn't start with a forbidden character
    if sanitized.startswith(('_', '.', '-')):
        sanitized = 'container' + sanitized
    return sanitized

# --- Pydantic Models (subset of original, some are now in auth.py) ---

class Environment(BaseModel):
    id: str
    base_image: str
    status: str = "stopped"

class Project(BaseModel):
    name: str
    git_repo: str
    git_token: Optional[str] = None
    gemini_token: Optional[str] = None
    environments: List[Environment] = []

class ProjectCreate(BaseModel):
    name: str
    git_repo: str
    git_token: Optional[str] = None
    gemini_token: Optional[str] = None

class EnvironmentCreate(BaseModel):
    name: str
    base_image: str
    branch_mode: str
    existing_branch: Optional[str] = None

class ProjectSettingsUpdate(BaseModel):
    gemini_token: Optional[str] = None
    git_token: Optional[str] = None

# --- Authentication Endpoints ---

@auth_router.get("/auth/status")
def get_auth_status():
    """Check if any users exist in the system."""
    has_users = len(auth.get_users()) > 0
    return {"has_users": has_users}

@auth_router.post("/auth/initialize", response_model=User)
def initialize_first_user(user: UserCreate):
    """Create the very first user if none exist."""
    if len(auth.get_users()) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot initialize, a user already exists.",
        )
    
    try:
        created_user = auth.create_user(user)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Standard OAuth2 password flow to get a token."""
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/auth/register", response_model=User)
def register_user(user: UserCreate):
    """Allow anyone to register a new user."""
    try:
        # The create_user function already checks for duplicate usernames.
        created_user = auth.create_user(user)
        return created_user
    except ValueError as e:
        # This will catch the "Username already registered" error.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

# --- Protected API Endpoints ---

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    return project_service.get_projects()

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    try:
        new_project_data = Project(**project_data.dict(), environments=[])
        return project_service.create_project(new_project_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put("/projects/{project_name}/settings", response_model=Project)
async def update_project_settings(project_name: str, settings: ProjectSettingsUpdate, current_user: User = Depends(get_current_user)):
    updated_project = project_service.update_project(project_name, settings.dict(exclude_unset=True))
    if not updated_project:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")
    return updated_project

@api_router.get("/git/branches")
async def get_remote_branches(repo_url: str, token: Optional[str] = None, current_user: User = Depends(get_current_user)):
    try:
        return docker_service.list_remote_branches(repo_url, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/{project_name}/environments", response_model=Environment)
async def create_environment(project_name: str, env_data: EnvironmentCreate, current_user: User = Depends(get_current_user)):
    proj = project_service.get_project(project_name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    if any(e["id"] == env_data.name for e in proj.get("environments", [])):
        raise HTTPException(status_code=400, detail=f"Environment '{env_data.name}' already exists.")

    new_env = Environment(id=env_data.name, base_image=env_data.base_image)
    proj.setdefault("environments", []).append(new_env.dict())
    project_service.update_project(project_name, proj)

    try:
        # Sanitize names for Docker compatibility
        sane_project_name = sanitize_for_docker(project_name)
        sane_env_name = sanitize_for_docker(env_data.name)
        container_name = f"gemini-env-{sane_project_name}-{sane_env_name}"
        
        container_env_vars = {
            "GEMINI_API_KEY": proj.get("gemini_token", ""),
            "GIT_TOKEN": proj.get("git_token", "")
        }
        
        docker_service.create_and_run_environment(
            container_name=container_name, 
            base_image=env_data.base_image, 
            git_repo_url=proj["git_repo"],
            env_name=env_data.name, # Pass original name for git branch
            env_vars=container_env_vars,
            branch_mode=env_data.branch_mode,
            existing_branch=env_data.existing_branch
        )
        
        # Update status after successful creation
        for e in proj["environments"]:
            if e["id"] == env_data.name:
                e["status"] = "running"
                break
        project_service.update_project(project_name, proj)
        
        new_env.status = "running"
        return new_env

    except Exception as e:
        # Rollback: remove environment from project data if creation fails
        proj["environments"] = [env for env in proj["environments"] if env["id"] != env_data.name]
        project_service.update_project(project_name, proj)
        raise HTTPException(status_code=500, detail=f"Failed to create environment: {e}")

# ... (other endpoints need similar protection and service layer integration)
@api_router.get("/docker-images", response_model=List[str])
async def get_docker_images(current_user: User = Depends(get_current_user)):
    return docker_service.list_images()

@api_router.post("/projects/{project_name}/environments/{env_id}/stop", status_code=200)
async def stop_environment(project_name: str, env_id: str, current_user: User = Depends(get_current_user)):
    proj = project_service.get_project(project_name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    sane_project_name = sanitize_for_docker(project_name)
    sane_env_id = sanitize_for_docker(env_id)
    container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
    
    docker_service.stop_container(container_name)
    
    for e in proj.get("environments", []):
        if e["id"] == env_id:
            e["status"] = "stopped"
            break
    project_service.update_project(project_name, proj)
    
    return {"message": "Environment stopped."}

@api_router.delete("/projects/{project_name}/environments/{env_id}", status_code=204)
async def delete_environment(project_name: str, env_id: str, current_user: User = Depends(get_current_user)):
    proj = project_service.get_project(project_name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    sane_project_name = sanitize_for_docker(project_name)
    sane_env_id = sanitize_for_docker(env_id)
    container_name = f"gemini-env-{sane_project_name}-{sane_env_id}"
    
    docker_service.remove_container(container_name)
    
    proj["environments"] = [e for e in proj.get("environments", []) if e["id"] != env_id]
    project_service.update_project(project_name, proj)
    
    return
