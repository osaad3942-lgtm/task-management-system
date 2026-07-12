from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import (
    create_project,
    get_projects,
    get_project,
    update_project,
    delete_project
)

router = APIRouter()



@router.post("/projects", response_model=ProjectResponse)
def create(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can create projects"
        )

    return create_project(db, data, user_id=current_user.id)



@router.get("/projects", response_model=list[ProjectResponse])
def read_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or manager can view projects"
        )

    return get_projects(db)



@router.get("/projects/{project_id}", response_model=ProjectResponse)
def read_one(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or manager can view projects"
        )

    project = get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can update projects"
        )

    project = update_project(db, project_id, data)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.delete("/projects/{project_id}")
def delete(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can delete projects"
        )

    success = delete_project(db, project_id)

    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}