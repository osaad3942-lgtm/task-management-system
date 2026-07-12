from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime)

    projects = relationship("Project", back_populates="creator")
    tasks = relationship("Task", back_populates="assignee")