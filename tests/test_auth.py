import pytest
import bcrypt
from httpx import AsyncClient
from bson import ObjectId

from src.services import auth as auth_service
from src.schemas.users import UserRegister, UserLogin


def hash_password(password: str) -> str:
    """Hash password for test setup."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.mark.asyncio
async def test_register_attendee(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test successful attendee registration."""
    users_coll = mock_dependencies["users"]
    users_coll.find_one.return_value = None
    users_coll.insert_one.side_effect = lambda doc: doc.setdefault("_id", ObjectId())

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
    users_coll.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_register_organizer(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test successful organizer registration."""
    users_coll = mock_dependencies["users"]
    users_coll.find_one.return_value = None
    users_coll.insert_one.side_effect = lambda doc: doc.setdefault("_id", ObjectId())

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
async def test_register_duplicate_email(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test registration fails on duplicate email."""
    from pymongo.errors import DuplicateKeyError

    users_coll = mock_dependencies["users"]
    users_coll.insert_one.side_effect = DuplicateKeyError("duplicate key")

    with pytest.raises(ValueError, match="Email already registered"):
        auth_service.register_user(
            UserRegister(
                name="Duplicate",
                email="exists@example.com",
                password="SecurePass123",
                role="attendee",
            )
        )


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test successful login with valid credentials."""
    users_coll = mock_dependencies["users"]
    password = "SecurePass123"
    hashed = hash_password(password)

    users_coll.find_one.return_value = {
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
async def test_login_invalid_password(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test login fails with wrong password."""
    users_coll = mock_dependencies["users"]
    hashed = hash_password("CorrectPassword")
    users_coll.find_one.return_value = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "password_hash": hashed,
        "role": "attendee",
    }

    with pytest.raises(ValueError, match="Invalid credentials"):
        auth_service.login(
            UserLogin(email="alice@example.com", password="WrongPassword")
        )


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, mock_dependencies: dict) -> None:
    """Test login fails for non-existent user."""
    users_coll = mock_dependencies["users"]
    users_coll.find_one.return_value = None

    with pytest.raises(ValueError, match="Invalid credentials"):
        auth_service.login(
            UserLogin(email="nonexistent@example.com", password="AnyPassword")
        )
