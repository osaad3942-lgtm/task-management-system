"""
Tests for authentication endpoints (register & login).
"""
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


# ── Registration Tests ────────────────────────────────────────

def test_register_new_user():
    """Test successful registration with a unique email."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post(
        "/register",
        params={
            "name": "Test User",
            "email": unique_email,
            "password": "securepass123",
            "role": "employee"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"


def test_register_duplicate_email():
    """Test that registering with an existing email fails."""
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@test.com"
    # First registration
    client.post(
        "/register",
        params={
            "name": "User One",
            "email": unique_email,
            "password": "pass1",
            "role": "employee"
        }
    )
    # Second registration with same email
    response = client.post(
        "/register",
        params={
            "name": "User Two",
            "email": unique_email,
            "password": "pass2",
            "role": "employee"
        }
    )
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]


def test_register_with_different_roles():
    """Test registration with different roles (employee, manager, admin)."""
    for role in ["employee", "manager", "admin"]:
        unique_email = f"{role}_{uuid.uuid4().hex[:8]}@test.com"
        response = client.post(
            "/register",
            params={
                "name": f"Test {role.title()}",
                "email": unique_email,
                "password": "pass123",
                "role": role
            }
        )
        assert response.status_code == 200


# ── Login Tests ───────────────────────────────────────────────

def test_login_success():
    """Test successful login returns access_token, role, and user_id."""
    unique_email = f"login_{uuid.uuid4().hex[:8]}@test.com"
    # Register first
    client.post(
        "/register",
        params={
            "name": "Login User",
            "email": unique_email,
            "password": "mypassword",
            "role": "employee"
        }
    )
    # Login
    response = client.post(
        "/login",
        params={
            "email": unique_email,
            "password": "mypassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "employee"
    assert "user_id" in data


def test_login_wrong_password():
    """Test login with wrong password fails."""
    unique_email = f"wrongpw_{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/register",
        params={
            "name": "Wrong PW User",
            "email": unique_email,
            "password": "correctpassword",
            "role": "employee"
        }
    )
    response = client.post(
        "/login",
        params={
            "email": unique_email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Wrong email or password" in response.json()["detail"]


def test_login_nonexistent_email():
    """Test login with a non-existent email fails."""
    response = client.post(
        "/login",
        params={
            "email": "nonexistent@nowhere.com",
            "password": "whatever"
        }
    )
    assert response.status_code == 401
    assert "Wrong email or password" in response.json()["detail"]
