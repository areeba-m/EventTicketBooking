import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient
from bson import ObjectId

from src.dependencies.auth import get_current_user


@pytest.fixture
def fake_attendee_user() -> dict:
    """Fake authenticated attendee user."""
    return {
        "id": str(ObjectId()),
        "name": "Test Attendee",
        "email": "attendee@example.com",
        "role": "attendee",
        "bookings": [],
    }


@pytest.fixture
def override_auth_attendee(fake_attendee_user: dict) -> None:
    """Override auth dependency with fake attendee."""
    from src.main import app

    app.dependency_overrides[get_current_user] = lambda: fake_attendee_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test successful booking creation with adequate seats."""
    bookings_coll = mock_dependencies["bookings"]
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    events_coll.find_one.return_value = {
        "_id": ObjectId(event_id),
        "title": "Test Event",
        "available_seats": 50,
        "total_seats": 100,
        "bookings": [],
    }
    events_coll.find_one_and_update.return_value = {
        "_id": ObjectId(event_id),
        "available_seats": 48,
    }
    users_coll.find_one.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 201
    assert resp.json()["seats"] == 2
    assert resp.json()["status"] == "confirmed"
    bookings_coll.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_overbooking_denied(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test overbooking prevention when requesting more seats than available."""
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    # Only 1 seat available, but trying to book 5
    events_coll.find_one.return_value = {
        "_id": ObjectId(event_id),
        "title": "Test Event",
        "available_seats": 1,
        "total_seats": 100,
        "bookings": [],
    }
    # Simulate atomic check failing (not enough seats)
    events_coll.find_one_and_update.return_value = None
    users_coll.find_one.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }

    payload = {"event_id": event_id, "seats": 5}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "Not enough seats available" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_booking_zero_seats(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
) -> None:
    """Test booking fails with zero or negative seats."""
    event_id = str(ObjectId())
    payload = {"event_id": event_id, "seats": 0}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_booking_nonexistent_event(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking fails for non-existent event."""
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    events_coll.find_one.return_value = None
    users_coll.find_one.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "Event not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_booking_nonexistent_user(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking fails for non-existent user."""
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    event_id = str(ObjectId())

    events_coll.find_one.return_value = {
        "_id": ObjectId(event_id),
        "title": "Test Event",
        "available_seats": 50,
        "total_seats": 100,
        "bookings": [],
    }
    users_coll.find_one.return_value = None

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "User not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_list_user_bookings(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test listing user's bookings."""
    bookings_coll = mock_dependencies["bookings"]
    user_id = ObjectId(fake_attendee_user["id"])

    cursor = MagicMock()
    cursor.sort.return_value = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "event_id": ObjectId(),
            "seats": 2,
            "status": "confirmed",
            "created_at": "2026-04-28T12:00:00Z",
        }
    ]
    bookings_coll.find.return_value = cursor

    resp = await client.get("/bookings/me")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["seats"] == 2


@pytest.mark.asyncio
async def test_cancel_booking(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking cancellation restores seats to event."""
    bookings_coll = mock_dependencies["bookings"]
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    booking_id = str(ObjectId())
    event_id = ObjectId()
    user_id = ObjectId(fake_attendee_user["id"])

    bookings_coll.find_one.return_value = {
        "_id": ObjectId(booking_id),
        "user_id": user_id,
        "event_id": event_id,
        "seats": 2,
        "status": "confirmed",
        "created_at": "2026-04-28T12:00:00Z",
    }
    bookings_coll.find_one_and_update.return_value = {
        "_id": ObjectId(booking_id),
        "user_id": user_id,
        "event_id": event_id,
        "seats": 2,
        "status": "cancelled",
        "created_at": "2026-04-28T12:00:00Z",
    }

    resp = await client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    # Verify seats were incremented back
    events_coll.update_one.assert_any_call(
        {"_id": event_id},
        {"$inc": {"available_seats": 2}},
    )


@pytest.mark.asyncio
async def test_cancel_nonexistent_booking(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test canceling non-existent booking fails."""
    bookings_coll = mock_dependencies["bookings"]

    booking_id = str(ObjectId())
    bookings_coll.find_one.return_value = None

    resp = await client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 404
    assert "Booking not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test canceling already-cancelled booking returns it unchanged."""
    bookings_coll = mock_dependencies["bookings"]
    user_id = ObjectId(fake_attendee_user["id"])

    booking_id = str(ObjectId())
    bookings_coll.find_one.return_value = {
        "_id": ObjectId(booking_id),
        "user_id": user_id,
        "event_id": ObjectId(),
        "seats": 2,
        "status": "cancelled",
        "created_at": "2026-04-28T12:00:00Z",
    }

    resp = await client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_booking_race_condition_atomic(
    client: AsyncClient,
    mock_dependencies: dict,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test atomic seat reservation prevents race condition."""
    bookings_coll = mock_dependencies["bookings"]
    events_coll = mock_dependencies["events"]
    users_coll = mock_dependencies["users"]

    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    # Event has 2 seats left, two users try to book 2 seats each
    events_coll.find_one.return_value = {
        "_id": ObjectId(event_id),
        "available_seats": 2,
        "total_seats": 100,
        "bookings": [],
    }
    # First booking succeeds (find_one_and_update with $inc)
    events_coll.find_one_and_update.side_effect = [
        {"_id": ObjectId(event_id), "available_seats": 0},  # First succeeds
        None,  # Second fails (not enough seats)
    ]
    users_coll.find_one.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }

    # First booking succeeds
    payload1 = {"event_id": event_id, "seats": 2}
    resp1 = await client.post("/bookings", json=payload1)
    assert resp1.status_code == 201

    # Second booking from same user would fail if attempted (seats exhausted)
    # Mock another user attempt
    payload2 = {"event_id": event_id, "seats": 2}
    resp2 = await client.post("/bookings", json=payload2)
    assert resp2.status_code == 400
    assert "Not enough seats available" in resp2.json()["detail"]
