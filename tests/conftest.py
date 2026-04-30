import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.repositories.bookings import BookingRepository, get_booking_repository
from src.repositories.users import UserRepository, get_user_repository


@pytest.fixture
def mock_booking_repository() -> BookingRepository:
    return AsyncMock(spec=BookingRepository)


@pytest.fixture
def override_booking_repository(mock_booking_repository: BookingRepository) -> None:
    app.dependency_overrides[get_booking_repository] = lambda: mock_booking_repository
    yield
    app.dependency_overrides.pop(get_booking_repository, None)


@pytest.fixture
def mock_user_repository() -> UserRepository:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def override_user_repository(mock_user_repository: UserRepository) -> None:
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repository
    yield
    app.dependency_overrides.pop(get_user_repository, None)


@pytest_asyncio.fixture
async def client():
    """Create test client with mocked dependencies."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
