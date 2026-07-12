from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import get_cache, set_cache, delete_cache
from app.dependencies.auth import get_current_user
from app.models.task import Task
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import (
    create_task,
    get_tasks,
    get_task,
    update_task,
    delete_task
)

router = APIRouter()


def task_to_dict(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "project_id": task.project_id,
        "assignee_id": task.assignee_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }


@router.post("/tasks", response_model=TaskResponse)
def create(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = create_task(db, data, current_user)
    
    # Invalidate cache for current user (manager)
    delete_cache(f"tasks_{current_user.role}_{current_user.id}")
    
    # Invalidate cache for assigned employee (if task is assigned)
    if task.assignee_id:
        delete_cache(f"tasks_employee_{task.assignee_id}")
    
    return task


@router.get("/tasks", response_model=list[TaskResponse])
def read_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cache_key = f"tasks_{current_user.role}_{current_user.id}"

    cached = get_cache(cache_key)
    if cached:
        return cached

    tasks = get_tasks(db, current_user)
    tasks_data = [task_to_dict(task) for task in tasks]

    set_cache(cache_key, tasks_data, expire=600)

    return tasks_data


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def read_one(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = get_task(db, task_id, current_user)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get the task before update to track old assignee
    old_task = db.query(Task).filter(Task.id == task_id).first()
    old_assignee_id = old_task.assignee_id if old_task else None
    
    updated_task = update_task(db, task_id, data, current_user)

    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Invalidate cache for current user (manager)
    delete_cache(f"tasks_{current_user.role}_{current_user.id}")
    
    # Only handle assignee cache if the assignee field was actually provided in request
    if data.assignee_id is not None:
        # Invalidate cache for newly assigned employee (if assignee changed)
        if data.assignee_id != old_assignee_id:
            delete_cache(f"tasks_employee_{data.assignee_id}")
        
        # Invalidate cache for previously assigned employee (if they were assigned before)
        if old_assignee_id:
            delete_cache(f"tasks_employee_{old_assignee_id}")

    return updated_task


@router.delete("/tasks/{task_id}")
def delete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get the task before deletion to know who it's assigned to
    task_to_delete = db.query(Task).filter(Task.id == task_id).first()
    assignee_id = task_to_delete.assignee_id if task_to_delete else None
    
    success = delete_task(db, task_id, current_user)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    # Invalidate cache for current user (manager)
    delete_cache(f"tasks_{current_user.role}_{current_user.id}")
    
    # Invalidate cache for assigned employee (if task was assigned)
    if assignee_id:
        delete_cache(f"tasks_employee_{assignee_id}")

    return {"message": "Task deleted successfully"}