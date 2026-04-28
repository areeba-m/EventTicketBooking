from pymongo.collection import Collection

from src.db.connection import get_database


def users_collection() -> Collection:
    return get_database()["users"]


def events_collection() -> Collection:
    return get_database()["events"]


def bookings_collection() -> Collection:
    return get_database()["bookings"]
