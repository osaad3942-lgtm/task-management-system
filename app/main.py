from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.middleware.logging_middleware import LoggingMiddleware
from app.core.database import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.routes.monitoring import router as monitoring_router
from app.routes.auth import router as auth_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management System")

# THIS IS REQUIRED - without it browser blocks all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth_router, tags=["Auth"])
app.include_router(project_router, tags=["Projects"])
app.include_router(task_router, tags=["Tasks"])
app.include_router(monitoring_router, tags=["Monitoring"])

# Serve index.html at http://localhost:8000/app
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")

@app.get("/app")
def serve_frontend():
    return FileResponse(FRONTEND_PATH)

@app.get("/")
def home():
    return {"message": "API Running Successfully"}