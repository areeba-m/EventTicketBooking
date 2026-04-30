from pymongo.collection import Collection
from pymongo.read_preferences import ReadPreference

from src.db.connection import get_database


def users_collection() -> Collection:
    return get_database()["users"]


def events_collection() -> Collection:
    return get_database()["events"]


def bookings_collection() -> Collection:
    return get_database()["bookings"]


def analytics_users_collection() -> Collection:
    return get_database()["users"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )


def analytics_events_collection() -> Collection:
    return get_database()["events"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )


def analytics_bookings_collection() -> Collection:
    return get_database()["bookings"].with_options(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )
