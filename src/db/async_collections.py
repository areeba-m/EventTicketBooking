from pymongo.asynchronous.collection import AsyncCollection
from pymongo.read_preferences import ReadPreference

from src.db.async_connection import get_async_database


def async_users_collection() -> AsyncCollection:
    return get_async_database()["users"]


def async_events_collection() -> AsyncCollection:
    return get_async_database()["events"]


def async_bookings_collection() -> AsyncCollection:
    return get_async_database()["bookings"]


def async_analytics_users_collection() -> AsyncCollection:
    return get_async_database()["users"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )


def async_analytics_events_collection() -> AsyncCollection:
    return get_async_database()["events"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )


def async_analytics_bookings_collection() -> AsyncCollection:
    return get_async_database()["bookings"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )
