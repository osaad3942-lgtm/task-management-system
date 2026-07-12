"""
Tests for project endpoints (CRUD operations with role-based access).
"""
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def _create_user_and_login(role="admin"):
    """Helper: register a user with the given role and return the auth token."""
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


# ── Project Creation Tests ────────────────────────────────────

def test_admin_can_create_project():
    """Admin should be able to create a project."""
    token, _ = _create_user_and_login("admin")
    response = client.post(
        "/projects",
        json={"name": f"Project {uuid.uuid4().hex[:6]}", "description": "Test project"},
        headers=_auth_header(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["description"] == "Test project"


def test_manager_cannot_create_project():
    """Manager should NOT be able to create projects."""
    token, _ = _create_user_and_login("manager")
    response = client.post(
        "/projects",
        json={"name": "Manager Project", "description": "Should fail"},
        headers=_auth_header(token)
    )
    assert response.status_code == 403


def test_employee_cannot_create_project():
    """Employee should NOT be able to create projects."""
    token, _ = _create_user_and_login("employee")
    response = client.post(
        "/projects",
        json={"name": "Employee Project", "description": "Should fail"},
        headers=_auth_header(token)
    )
    assert response.status_code == 403


def test_create_project_without_token():
    """Creating a project without a token should fail (401/403)."""
    response = client.post(
        "/projects",
        json={"name": "Unauthorized", "description": "Should fail"}
    )
    assert response.status_code in [401, 403]


# ── Project Read Tests ────────────────────────────────────────

def test_admin_can_list_projects():
    """Admin should be able to list all projects."""
    token, _ = _create_user_and_login("admin")
    response = client.get(
        "/projects",
        headers=_auth_header(token)
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_manager_can_list_projects():
    """Manager should be able to list all projects."""
    token, _ = _create_user_and_login("manager")
    response = client.get(
        "/projects",
        headers=_auth_header(token)
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_employee_cannot_list_projects():
    """Employee should NOT be able to list projects."""
    token, _ = _create_user_and_login("employee")
    response = client.get(
        "/projects",
        headers=_auth_header(token)
    )
    assert response.status_code == 403


# ── Project Update Tests ──────────────────────────────────────

def test_admin_can_update_project():
    """Admin should be able to update a project."""
    token, _ = _create_user_and_login("admin")
    # Create first
    create_resp = client.post(
        "/projects",
        json={"name": f"Update Me {uuid.uuid4().hex[:6]}", "description": "Original"},
        headers=_auth_header(token)
    )
    project_id = create_resp.json()["id"]

    # Update
    response = client.put(
        f"/projects/{project_id}",
        json={"name": "Updated Name", "description": "Updated desc"},
        headers=_auth_header(token)
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_manager_cannot_update_project():
    """Manager should NOT be able to update projects."""
    # Create with admin
    admin_token, _ = _create_user_and_login("admin")
    create_resp = client.post(
        "/projects",
        json={"name": f"No Manager Update {uuid.uuid4().hex[:6]}", "description": "test"},
        headers=_auth_header(admin_token)
    )
    project_id = create_resp.json()["id"]

    # Try update with manager
    manager_token, _ = _create_user_and_login("manager")
    response = client.put(
        f"/projects/{project_id}",
        json={"name": "Should Fail"},
        headers=_auth_header(manager_token)
    )
    assert response.status_code == 403


# ── Project Delete Tests ──────────────────────────────────────

def test_admin_can_delete_project():
    """Admin should be able to delete a project."""
    token, _ = _create_user_and_login("admin")
    create_resp = client.post(
        "/projects",
        json={"name": f"Delete Me {uuid.uuid4().hex[:6]}", "description": "test"},
        headers=_auth_header(token)
    )
    project_id = create_resp.json()["id"]

    response = client.delete(
        f"/projects/{project_id}",
        headers=_auth_header(token)
    )
    assert response.status_code == 200


def test_update_nonexistent_project():
    """Updating a non-existent project should return 404."""
    token, _ = _create_user_and_login("admin")
    response = client.put(
        "/projects/999999",
        json={"name": "Ghost"},
        headers=_auth_header(token)
    )
    assert response.status_code == 404


def test_delete_nonexistent_project():
    """Deleting a non-existent project should return 404."""
    token, _ = _create_user_and_login("admin")
    response = client.delete(
        "/projects/999999",
        headers=_auth_header(token)
    )
    assert response.status_code == 404
