from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(20), default="todo", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    assignee_id = Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    assignee = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")