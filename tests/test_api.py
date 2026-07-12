from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "API Running Successfully"


def test_register_user():
    response = client.post(
        "/register",
        params={
            "name": "Test User",
            "email": "test_user_api@test.com",
            "password": "1234",
            "role": "employee"
        }
    )

    assert response.status_code in [200, 400]


def test_login_admin():
    response = client.post(
        "/login",
        params={
            "email": "admin4@test.com",
            "password": "123"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def get_admin_token():
    response = client.post(
        "/login",
        params={
            "email": "admin4@test.com",
            "password": "123"
        }
    )

    return response.json()["access_token"]


def get_employee_token():
    response = client.post(
        "/login",
        params={
            "email": "omar@gmail.com",
            "password": "123"
        }
    )

    return response.json()["access_token"]


def test_tasks_without_token_blocked():
    response = client.get("/tasks")
    assert response.status_code in [401, 403]


def test_projects_create_without_token_blocked():
    response = client.post(
        "/projects",
        json={
            "name": "Unauthorized Project",
            "description": "Should fail"
        }
    )

    assert response.status_code in [401, 403]


def test_admin_can_create_project():
    token = get_admin_token()

    response = client.post(
        "/projects",
        json={
            "name": "Pytest Project",
            "description": "Created from pytest"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Pytest Project"
    assert "id" in data


def test_admin_can_get_projects():
    token = get_admin_token()

    response = client.get(
        "/projects",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_employee_cannot_create_project():
    token = get_employee_token()

    response = client.post(
        "/projects",
        json={
            "name": "Employee Project",
            "description": "Should not be allowed"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_create_task_invalid_project():
    token = get_admin_token()

    response = client.post(
        "/tasks",
        json={
            "title": "Invalid Project Task",
            "description": "This should fail",
            "project_id": 999999,
            "assignee_id": 3,
            "priority": "high"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code in [400, 404]


def test_invalid_task_status_transition():
    token = get_admin_token()

    # create project first
    project_response = client.post(
        "/projects",
        json={
            "name": "Transition Test Project",
            "description": "project for testing"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    project_id = project_response.json()["id"]

    # create task with todo status
    task_response = client.post(
        "/tasks",
        json={
            "title": "Transition Test Task",
            "description": "testing invalid transition",
            "project_id": project_id,
            "assignee_id": 3,
            "priority": "high"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    task_id = task_response.json()["id"]

    # invalid transition: todo -> done
    response = client.put(
        f"/tasks/{task_id}",
        json={
            "status": "done"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400