import json
import traceback
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from .services import docker_service

router = APIRouter()

# --- Database Setup ---
DB_PATH = Path(__file__).parent.parent / "data" / "projects.json"
DB_PATH.parent.mkdir(exist_ok=True)

def read_db():
    if not DB_PATH.exists():
        DB_PATH.write_text("[]")
    with open(DB_PATH, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

# --- Pydantic Models ---
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
    branch_mode: str # 'new' or 'existing'
    existing_branch: Optional[str] = None

class ProjectSettingsUpdate(BaseModel):
    gemini_token: Optional[str] = None
    git_token: Optional[str] = None

# --- Helper Functions ---
def find_project_or_404(project_name: str, db: list):
    for i, proj in enumerate(db):
        if proj["name"] == project_name:
            return i, proj
    raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

# --- API Endpoints ---

@router.get("/git/branches")
async def get_remote_branches(repo_url: str, token: Optional[str] = None):
    """Lists all branches for a given remote git repository."""
    try:
        return docker_service.list_remote_branches(repo_url, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_name}/environments", response_model=Environment)
async def create_environment(project_name: str, env_data: EnvironmentCreate):
    db = read_db()
    idx, proj = find_project_or_404(project_name, db)
    
    if "environments" not in proj:
        proj["environments"] = []
    
    if any(e["id"] == env_data.name for e in proj["environments"]):
        raise HTTPException(status_code=400, detail=f"Environment '{env_data.name}' already exists.")

    new_env = Environment(id=env_data.name, base_image=env_data.base_image)
    proj["environments"].append(new_env.model_dump())
    write_db(db)
    
    try:
        container_name = f"gemini-env-{project_name}-{env_data.name}"
        container_env_vars = {
            "GEMINI_API_KEY": proj.get("gemini_token", ""),
            "GIT_TOKEN": proj.get("git_token", "")
        }
        
        docker_service.create_and_run_environment(
            container_name=container_name, 
            base_image=env_data.base_image, 
            git_repo_url=proj["git_repo"],
            env_name=env_data.name,
            env_vars=container_env_vars,
            branch_mode=env_data.branch_mode,
            existing_branch=env_data.existing_branch
        )
        
        for e in proj["environments"]:
            if e["id"] == env_data.name:
                e["status"] = "running"
                break
        write_db(db)
        
        new_env.status = "running"
        return new_env

    except Exception as e:
        traceback.print_exc()
        proj["environments"] = [env for env in proj["environments"] if env["id"] != env_data.name]
        write_db(db)
        raise HTTPException(status_code=500, detail=f"Failed to create environment: {e}")

# ... (other endpoints remain the same)
@router.get("/projects", response_model=List[Project])
async def get_projects():
    return read_db()

@router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate):
    db = read_db()
    if any(p["name"] == project_data.name for p in db):
        raise HTTPException(status_code=400, detail=f"Project '{project_data.name}' already exists.")
    new_project = Project(**project_data.model_dump(), environments=[])
    db.append(new_project.model_dump())
    write_db(db)
    return new_project

@router.put("/projects/{project_name}/settings", response_model=Project)
async def update_project_settings(project_name: str, settings: ProjectSettingsUpdate):
    db = read_db()
    idx, proj = find_project_or_404(project_name, db)
    if settings.gemini_token is not None:
        proj["gemini_token"] = settings.gemini_token
    if settings.git_token is not None:
        proj["git_token"] = settings.git_token
    write_db(db)
    return proj

@router.delete("/projects/{project_name}", status_code=204)
async def delete_project(project_name: str):
    db = read_db()
    idx, proj = find_project_or_404(project_name, db)
    for env in proj.get("environments", []):
        docker_service.remove_container(f"gemini-env-{project_name}-{env['id']}")
    db.pop(idx)
    write_db(db)
    return

@router.get("/docker-images", response_model=List[str])
async def get_docker_images():
    return docker_service.list_images()

@router.post("/projects/{project_name}/environments/{env_id}/stop", status_code=200)
async def stop_environment(project_name: str, env_id: str):
    container_name = f"gemini-env-{project_name}-{env_id}"
    docker_service.stop_container(container_name)
    db = read_db()
    idx, proj = find_project_or_404(project_name, db)
    for e in proj["environments"]:
        if e["id"] == env_id:
            e["status"] = "stopped"
            break
    write_db(db)
    return {"message": "Environment stopped."}

@router.delete("/projects/{project_name}/environments/{env_id}", status_code=204)
async def delete_environment(project_name: str, env_id: str):
    db = read_db()
    idx, proj = find_project_or_404(project_name, db)
    container_name = f"gemini-env-{project_name}-{env_id}"
    docker_service.remove_container(container_name)
    proj["environments"] = [e for e in proj["environments"] if e["id"] != env_id]
    write_db(db)
    return