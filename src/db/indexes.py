from src.db.collections import bookings_collection, events_collection, users_collection


def ensure_indexes() -> None:
    users_collection().create_index("email", unique=True)
    events_collection().create_index("date")
    events_collection().create_index("venue")
    bookings_collection().create_index("user_id")
    bookings_collection().create_index("event_id")
