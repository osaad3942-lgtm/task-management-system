from sqlalchemy.orm import Session
from datetime import datetime

from app.models.project import Project
from app.models.task import Task
from app.utils.logger import logger


def create_project(db: Session, data, user_id: int):
    project = Project(
        name=data.name,
        description=data.description,
        created_by=user_id,
        created_at=datetime.utcnow()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"Project created | project_id={project.id} | created_by={user_id}")

    return project


def get_projects(db: Session):
    logger.debug("Database query | get all projects")
    return db.query(Project).all()


def get_project(db: Session, project_id: int):
    logger.debug(f"Database query | get project | project_id={project_id}")
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: int, data):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        logger.warning(f"Project not found | project_id={project_id}")
        return None

    if data.name is not None:
        project.name = data.name

    if data.description is not None:
        project.description = data.description

    db.commit()
    db.refresh(project)

    logger.info(f"Project updated | project_id={project_id}")

    return project


def delete_project(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        logger.warning(f"Project not found | project_id={project_id}")
        return False

    db.query(Task).filter(Task.project_id == project_id).delete()

    db.delete(project)
    db.commit()

    logger.info(f"Project deleted | project_id={project_id}")

    return True