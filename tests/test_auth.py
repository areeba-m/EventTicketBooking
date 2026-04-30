import pytest
import bcrypt
from httpx import AsyncClient
from bson import ObjectId



def hash_password(password: str) -> str:
    """Hash password for test setup."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.mark.asyncio
async def test_register_attendee(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test successful attendee registration."""
    mock_user_repository.insert_user.return_value = None

    payload = {
        "name": "Alice Attendee",
        "email": "alice@example.com",
        "password": "SecurePass123",
        "role": "attendee",
    }
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Alice Attendee"
    assert resp.json()["role"] == "attendee"
    mock_user_repository.insert_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_organizer(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test successful organizer registration."""
    mock_user_repository.insert_user.return_value = None

    payload = {
        "name": "Olivia Organizer",
        "email": "olivia@example.com",
        "password": "SecurePass123",
        "role": "organizer",
    }
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["role"] == "organizer"


@pytest.mark.asyncio
async def test_register_duplicate_email(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test registration fails on duplicate email."""
    from pymongo.errors import DuplicateKeyError

    mock_user_repository.insert_user.side_effect = DuplicateKeyError("duplicate key")

    payload = {
        "name": "Duplicate",
        "email": "exists@example.com",
        "password": "SecurePass123",
        "role": "attendee",
    }
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_valid_credentials(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test successful login with valid credentials."""
    password = "SecurePass123"
    hashed = hash_password(password)

    mock_user_repository.get_user_by_email.return_value = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "password_hash": hashed,
        "role": "attendee",
    }

    payload = {"email": "alice@example.com", "password": password}
    resp = await client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test login fails with wrong password."""
    hashed = hash_password("CorrectPassword")
    mock_user_repository.get_user_by_email.return_value = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "password_hash": hashed,
        "role": "attendee",
    }

    resp = await client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(
    client: AsyncClient,
    override_user_repository: None,
    mock_user_repository,
) -> None:
    """Test login fails for non-existent user."""
    mock_user_repository.get_user_by_email.return_value = None

    resp = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]
