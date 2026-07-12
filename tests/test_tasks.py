"""
Tests for task endpoints (CRUD, role-based access, status transitions, filtering).
"""
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def _create_user_and_login(role="admin"):
    """Helper: register a user with the given role and return the auth token + user_id."""
    unique_email = f"{role}_{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/register",
        params={
            "name": f"Test {role.title()}",
            "email": unique_email,
            "password": "testpass",
            "role": role
        }
    )
    resp = client.post(
        "/login",
        params={
            "email": unique_email,
            "password": "testpass"
        }
    )
    data = resp.json()
    return data["access_token"], data.get("user_id")


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_project(token):
    """Helper: create a project and return its ID."""
    resp = client.post(
        "/projects",
        json={"name": f"TaskTest Project {uuid.uuid4().hex[:6]}", "description": "For task tests"},
        headers=_auth_header(token)
    )
    return resp.json()["id"]


# ── Access Control Tests ──────────────────────────────────────

def test_home():
    """Home endpoint should return 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_get_tasks_unauthorized():
    """Getting tasks without a token should fail."""
    response = client.get("/tasks")
    assert response.status_code in [401, 403]


# ── Task Creation Tests ──────────────────────────────────────

def test_admin_can_create_task():
    """Admin should be able to create a task."""
    admin_token, _ = _create_user_and_login("admin")
    employee_token, employee_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    response = client.post(
        "/tasks",
        json={
            "title": f"Test Task {uuid.uuid4().hex[:6]}",
            "description": "A test task",
            "project_id": project_id,
            "assignee_id": employee_id,
            "priority": "high"
        },
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"].startswith("Test Task")
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["assignee_id"] == employee_id


def test_manager_can_create_task():
    """Manager should be able to create a task."""
    admin_token, _ = _create_user_and_login("admin")
    manager_token, _ = _create_user_and_login("manager")
    employee_token, employee_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    response = client.post(
        "/tasks",
        json={
            "title": "Manager Task",
            "description": "Created by manager",
            "project_id": project_id,
            "assignee_id": employee_id,
            "priority": "medium"
        },
        headers=_auth_header(manager_token)
    )
    assert response.status_code == 200


def test_employee_cannot_create_task():
    """Employee should NOT be able to create tasks."""
    admin_token, _ = _create_user_and_login("admin")
    employee_token, employee_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    response = client.post(
        "/tasks",
        json={
            "title": "Employee Task",
            "description": "Should fail",
            "project_id": project_id,
            "priority": "low"
        },
        headers=_auth_header(employee_token)
    )
    assert response.status_code == 403


def test_create_task_invalid_project():
    """Creating a task with a non-existent project should fail."""
    admin_token, _ = _create_user_and_login("admin")
    response = client.post(
        "/tasks",
        json={
            "title": "Bad Project Task",
            "description": "Should fail",
            "project_id": 999999,
            "priority": "high"
        },
        headers=_auth_header(admin_token)
    )
    assert response.status_code in [400, 404]


def test_create_task_without_assignee():
    """Creating a task without an assignee should succeed."""
    admin_token, _ = _create_user_and_login("admin")
    project_id = _create_project(admin_token)

    response = client.post(
        "/tasks",
        json={
            "title": "Unassigned Task",
            "description": "No assignee",
            "project_id": project_id,
            "priority": "low"
        },
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["assignee_id"] is None


def test_create_task_assign_to_non_employee():
    """Assigning a task to a non-employee (manager/admin) should fail."""
    admin_token, admin_id = _create_user_and_login("admin")
    project_id = _create_project(admin_token)

    response = client.post(
        "/tasks",
        json={
            "title": "Bad Assignee Task",
            "project_id": project_id,
            "assignee_id": admin_id,
            "priority": "high"
        },
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 400


# ── Task Read Tests ───────────────────────────────────────────

def test_admin_can_list_all_tasks():
    """Admin should see all tasks."""
    admin_token, _ = _create_user_and_login("admin")
    response = client.get(
        "/tasks",
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_employee_sees_only_assigned_tasks():
    """Employee should only see tasks assigned to them."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    # Create a task assigned to this employee
    client.post(
        "/tasks",
        json={
            "title": "Assigned Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )

    # Employee lists tasks
    response = client.get(
        "/tasks",
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 200
    tasks = response.json()
    for task in tasks:
        assert task["assignee_id"] == emp_id


# ── Task Status Transition Tests ──────────────────────────────

def test_valid_status_transition_todo_to_in_progress():
    """todo -> in_progress should succeed."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Transition Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    # Employee changes status: todo -> in_progress
    response = client.put(
        f"/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_valid_status_transition_in_progress_to_done():
    """in_progress -> done should succeed."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Complete Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    # todo -> in_progress
    client.put(
        f"/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=_auth_header(emp_token)
    )
    # in_progress -> done
    response = client.put(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_invalid_status_transition_todo_to_done():
    """todo -> done (skipping in_progress) should fail."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Skip Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    # todo -> done (invalid)
    response = client.put(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 400


def test_invalid_status_value():
    """Using an invalid status string should fail."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Bad Status Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={"status": "invalid_status"},
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 400


# ── Employee Restrictions ─────────────────────────────────────

def test_employee_cannot_update_title():
    """Employee should NOT be able to change task title."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Original Title",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Hacked Title"},
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 403


def test_employee_cannot_delete_task():
    """Employee should NOT be able to delete tasks."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "No Delete",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "medium"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers=_auth_header(emp_token)
    )
    assert response.status_code == 403


# ── Task Update & Delete by Admin/Manager ─────────────────────

def test_admin_can_update_task_fields():
    """Admin should be able to update title, description, priority, and assignee."""
    admin_token, _ = _create_user_and_login("admin")
    emp_token, emp_id = _create_user_and_login("employee")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Admin Update Task",
            "project_id": project_id,
            "assignee_id": emp_id,
            "priority": "low"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Updated by Admin",
            "description": "New description",
            "priority": "high"
        },
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated by Admin"
    assert data["description"] == "New description"
    assert data["priority"] == "high"


def test_admin_can_delete_task():
    """Admin should be able to delete a task."""
    admin_token, _ = _create_user_and_login("admin")
    project_id = _create_project(admin_token)

    create_resp = client.post(
        "/tasks",
        json={
            "title": "Delete This",
            "project_id": project_id,
            "priority": "low"
        },
        headers=_auth_header(admin_token)
    )
    task_id = create_resp.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 200


def test_delete_nonexistent_task():
    """Deleting a non-existent task should return 404."""
    admin_token, _ = _create_user_and_login("admin")
    response = client.delete(
        "/tasks/999999",
        headers=_auth_header(admin_token)
    )
    assert response.status_code == 404