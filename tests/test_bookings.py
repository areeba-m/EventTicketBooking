import pytest
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
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test successful booking creation with adequate seats."""
    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    mock_booking_repository.get_user.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }
    mock_booking_repository.get_event.return_value = {
        "_id": ObjectId(event_id),
        "title": "Test Event",
        "available_seats": 50,
        "total_seats": 100,
        "bookings": [],
    }
    mock_booking_repository.reserve_event_seats.return_value = {
        "_id": ObjectId(event_id),
        "available_seats": 48,
    }
    mock_booking_repository.insert_booking.return_value = None
    mock_booking_repository.append_user_booking_summary.return_value = None
    mock_booking_repository.append_event_booking_summary.return_value = None

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 201
    assert resp.json()["seats"] == 2
    assert resp.json()["status"] == "confirmed"
    mock_booking_repository.insert_booking.assert_awaited_once()


@pytest.mark.asyncio
async def test_overbooking_denied(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test overbooking prevention when requesting more seats than available."""
    event_id = str(ObjectId())

    mock_booking_repository.get_user.return_value = {
        "_id": ObjectId(fake_attendee_user["id"]),
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }
    mock_booking_repository.get_event.return_value = {
        "_id": ObjectId(event_id),
        "title": "Test Event",
        "available_seats": 1,
        "total_seats": 100,
        "bookings": [],
    }
    mock_booking_repository.reserve_event_seats.return_value = None

    payload = {"event_id": event_id, "seats": 5}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "Not enough seats available" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_booking_zero_seats(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
) -> None:
    """Test booking fails with zero or negative seats."""
    event_id = str(ObjectId())
    payload = {"event_id": event_id, "seats": 0}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 422  # Pydantic validation error
    mock_booking_repository.get_user.assert_not_called()


@pytest.mark.asyncio
async def test_booking_nonexistent_event(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking fails for non-existent event."""
    event_id = str(ObjectId())

    mock_booking_repository.get_user.return_value = {
        "_id": ObjectId(fake_attendee_user["id"]),
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }
    mock_booking_repository.get_event.return_value = None

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "Event not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_booking_nonexistent_user(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking fails for non-existent user."""
    event_id = str(ObjectId())

    mock_booking_repository.get_user.return_value = None

    payload = {"event_id": event_id, "seats": 2}
    resp = await client.post("/bookings", json=payload)
    assert resp.status_code == 400
    assert "User not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_list_user_bookings(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test listing user's bookings."""
    user_id = ObjectId(fake_attendee_user["id"])

    mock_booking_repository.list_bookings_for_user.return_value = [
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "event_id": ObjectId(),
            "seats": 2,
            "status": "confirmed",
            "created_at": "2026-04-28T12:00:00Z",
        }
    ]

    resp = await client.get("/bookings/me")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["seats"] == 2


@pytest.mark.asyncio
async def test_list_users_by_status(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
) -> None:
    """Test listing users by booking status."""

    mock_booking_repository.list_users_by_status.return_value = [
        {
            "_id": ObjectId(),
            "name": "Alice",
            "email": "alice@example.com",
            "status": "confirmed",
        }
    ]

    resp = await client.get("/bookings/confirmed")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Alice"
    assert resp.json()[0]["status"] == "confirmed"
    mock_booking_repository.list_users_by_status.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_users_by_status_invalid(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
) -> None:
    """Test listing users by status rejects invalid status values."""
    resp = await client.get("/bookings/pending")
    assert resp.status_code == 400
    assert "Invalid booking status" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_booking(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test booking cancellation restores seats to event."""
    booking_id = str(ObjectId())
    event_id = ObjectId()
    user_id = ObjectId(fake_attendee_user["id"])

    mock_booking_repository.get_booking.return_value = {
        "_id": ObjectId(booking_id),
        "user_id": user_id,
        "event_id": event_id,
        "seats": 2,
        "status": "confirmed",
        "created_at": "2026-04-28T12:00:00Z",
    }
    mock_booking_repository.mark_booking_cancelled.return_value = {
        "_id": ObjectId(booking_id),
        "user_id": user_id,
        "event_id": event_id,
        "seats": 2,
        "status": "cancelled",
        "created_at": "2026-04-28T12:00:00Z",
    }
    mock_booking_repository.release_event_seats.return_value = None
    mock_booking_repository.set_user_booking_status.return_value = None
    mock_booking_repository.set_event_booking_status.return_value = None

    resp = await client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    mock_booking_repository.mark_booking_cancelled.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_nonexistent_booking(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test canceling non-existent booking fails."""
    booking_id = str(ObjectId())
    mock_booking_repository.get_booking.return_value = None

    resp = await client.delete(f"/bookings/{booking_id}")
    assert resp.status_code == 404
    assert "Booking not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(
    client: AsyncClient,
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test canceling already-cancelled booking returns it unchanged."""
    user_id = ObjectId(fake_attendee_user["id"])

    booking_id = str(ObjectId())
    mock_booking_repository.get_booking.return_value = {
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
    override_booking_repository: None,
    mock_booking_repository,
    override_auth_attendee: None,
    fake_attendee_user: dict,
) -> None:
    """Test atomic seat reservation prevents race condition."""
    event_id = str(ObjectId())
    user_id = ObjectId(fake_attendee_user["id"])

    mock_booking_repository.get_user.return_value = {
        "_id": user_id,
        "email": fake_attendee_user["email"],
        "role": "attendee",
    }
    mock_booking_repository.get_event.return_value = {
        "_id": ObjectId(event_id),
        "available_seats": 2,
        "total_seats": 100,
        "bookings": [],
    }
    mock_booking_repository.reserve_event_seats.side_effect = [
        {"_id": ObjectId(event_id), "available_seats": 0},
        None,
    ]
    mock_booking_repository.insert_booking.return_value = None
    mock_booking_repository.append_user_booking_summary.return_value = None
    mock_booking_repository.append_event_booking_summary.return_value = None

    payload1 = {"event_id": event_id, "seats": 2}
    resp1 = await client.post("/bookings", json=payload1)
    assert resp1.status_code == 201

    payload2 = {"event_id": event_id, "seats": 2}
    resp2 = await client.post("/bookings", json=payload2)
    assert resp2.status_code == 400
    assert "Not enough seats available" in resp2.json()["detail"]
