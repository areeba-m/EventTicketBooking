import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from pymongo.collection import Collection

from src.main import app
from src.db import connection as db_connection
from src.db.collections import bookings_collection, events_collection, users_collection


@pytest.fixture
def mock_collection() -> Collection:
    """Create a mock MongoDB collection."""
    return MagicMock(spec=Collection)


@pytest.fixture
def mock_users_collection(mock_collection: Collection) -> Collection:
    """Mock users collection with sample data."""
    collection = MagicMock(spec=Collection)
    collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Test User",
        "email": "test@example.com",
        "role": "attendee",
        "password_hash": "$2b$12$...",
        "bookings": [],
    }
    collection.insert_one = MagicMock()
    return collection


@pytest.fixture
def mock_events_collection(mock_collection: Collection) -> Collection:
    """Mock events collection with sample data."""
    collection = MagicMock(spec=Collection)
    collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "title": "Test Event",
        "date": "2026-06-15T19:00:00Z",
        "venue": "Test Hall",
        "total_seats": 100,
        "available_seats": 50,
        "bookings": [],
    }
    collection.find.return_value = []
    collection.find_one_and_update = MagicMock(
        return_value={
            "_id": "507f1f77bcf86cd799439012",
            "available_seats": 48,
        }
    )
    collection.insert_one = MagicMock()
    collection.update_one = MagicMock()
    return collection


@pytest.fixture
def mock_bookings_collection(mock_collection: Collection) -> Collection:
    """Mock bookings collection."""
    collection = MagicMock(spec=Collection)
    collection.find.return_value = []
    collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439013",
        "user_id": "507f1f77bcf86cd799439011",
        "event_id": "507f1f77bcf86cd799439012",
        "seats": 2,
        "status": "confirmed",
        "created_at": "2026-04-28T12:00:00Z",
    }
    collection.insert_one = MagicMock()
    collection.find_one_and_update = MagicMock(
        return_value={
            "_id": "507f1f77bcf86cd799439013",
            "status": "cancelled",
        }
    )
    collection.aggregate = MagicMock(return_value=[])
    return collection


@pytest.fixture
def mock_dependencies(
    mock_users_collection: Collection,
    mock_events_collection: Collection,
    mock_bookings_collection: Collection,
) -> dict:
    """Override app dependencies with mocks."""
    mock_db = MagicMock()
    collection_map = {
        "users": mock_users_collection,
        "events": mock_events_collection,
        "bookings": mock_bookings_collection,
    }
    mock_db.__getitem__.side_effect = lambda name: collection_map[name]
    db_connection._db = mock_db

    app.dependency_overrides[users_collection] = lambda: mock_users_collection
    app.dependency_overrides[events_collection] = lambda: mock_events_collection
    app.dependency_overrides[bookings_collection] = lambda: mock_bookings_collection
    yield {
        "users": mock_users_collection,
        "events": mock_events_collection,
        "bookings": mock_bookings_collection,
    }
    app.dependency_overrides.clear()
    db_connection._db = None


@pytest_asyncio.fixture
async def client(mock_dependencies: dict):
    """Create test client with mocked dependencies."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
