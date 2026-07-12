from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.task import Task
from app.models.user import User
from app.models.project import Project
from app.utils.helpers import validate_status_transition
from app.utils.logger import logger


def create_task(db: Session, data, current_user):
    if current_user.role not in ["admin", "manager"]:
        logger.warning(
            f"Forbidden task create | user_id={current_user.id} | role={current_user.role}"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admin or manager can create tasks"
        )

    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        logger.warning(f"Task create failed | project_id={data.project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    if data.assignee_id:
        assignee = db.query(User).filter(User.id == data.assignee_id).first()

        if not assignee:
            logger.warning(f"Task create failed | assignee_id={data.assignee_id} not found")
            raise HTTPException(status_code=404, detail="Assignee user not found")

        if assignee.role != "employee":
            logger.warning(
                f"Task create failed | assignee_id={data.assignee_id} "
                f"| role={assignee.role} | reason=not_employee"
            )
            raise HTTPException(
                status_code=400,
                detail="Tasks can only be assigned to employees"
            )

    task = Task(
        title=data.title,
        description=data.description,
        project_id=data.project_id,
        assignee_id=data.assignee_id,
        priority=data.priority or "medium",
        status="todo",
        created_at=datetime.utcnow()
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info(
        f"Task created | task_id={task.id} | project_id={task.project_id} "
        f"| assignee_id={task.assignee_id} | created_by={current_user.id}"
    )

    return task


def get_tasks(db: Session, current_user):
    logger.debug(
        f"Database query | get tasks | user_id={current_user.id} | role={current_user.role}"
    )

    if current_user.role in ["admin", "manager"]:
        return db.query(Task).all()

    return db.query(Task).filter(Task.assignee_id == current_user.id).all()


def get_task(db: Session, task_id: int, current_user):
    logger.debug(
        f"Database query | get task | task_id={task_id} "
        f"| user_id={current_user.id} | role={current_user.role}"
    )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        logger.warning(f"Task not found | task_id={task_id}")
        return None

    if current_user.role == "employee" and task.assignee_id != current_user.id:
        logger.warning(
            f"Forbidden task view | task_id={task_id} "
            f"| user_id={current_user.id} | role={current_user.role}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only view your assigned tasks"
        )

    return task


def update_task(db: Session, task_id: int, data, current_user):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        logger.warning(f"Task not found | task_id={task_id}")
        return None

    if current_user.role == "employee":
        if task.assignee_id != current_user.id:
            logger.warning(
                f"Forbidden task update | task_id={task_id} "
                f"| user_id={current_user.id} | role={current_user.role}"
            )
            raise HTTPException(
                status_code=403,
                detail="You can only update your assigned tasks"
            )

        if (
            data.title is not None
            or data.description is not None
            or data.priority is not None
            or data.assignee_id is not None
        ):
            logger.warning(
                f"Forbidden employee update fields | task_id={task_id} "
                f"| user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=403,
                detail="Employee can only update task status"
            )

    if data.status is not None:
        old_status = task.status
        validate_status_transition(task.status, data.status)
        task.status = data.status

        logger.info(
            f"Task status updated | task_id={task_id} "
            f"| old_status={old_status} | new_status={task.status} "
            f"| user_id={current_user.id}"
        )

    if current_user.role in ["admin", "manager"]:
        if data.title is not None:
            task.title = data.title

        if data.description is not None:
            task.description = data.description

        if data.priority is not None:
            task.priority = data.priority

        if data.assignee_id is not None:
            assignee = db.query(User).filter(User.id == data.assignee_id).first()

            if not assignee:
                logger.warning(f"Task update failed | assignee_id={data.assignee_id} not found")
                raise HTTPException(status_code=404, detail="Assignee user not found")

            if assignee.role != "employee":
                logger.warning(
                    f"Task update failed | assignee_id={data.assignee_id} "
                    f"| role={assignee.role} | reason=not_employee"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Tasks can only be assigned to employees"
                )

            task.assignee_id = data.assignee_id

    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    logger.info(f"Task updated | task_id={task_id} | updated_by={current_user.id}")

    return task


def delete_task(db: Session, task_id: int, current_user):
    if current_user.role not in ["admin", "manager"]:
        logger.warning(
            f"Forbidden task delete | task_id={task_id} "
            f"| user_id={current_user.id} | role={current_user.role}"
        )
        raise HTTPException(
            status_code=403,
            detail="Only admin or manager can delete tasks"
        )

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        logger.warning(f"Task not found | task_id={task_id}")
        return False

    db.delete(task)
    db.commit()

    logger.info(f"Task deleted | task_id={task_id} | deleted_by={current_user.id}")

    return True