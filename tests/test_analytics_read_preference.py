from unittest.mock import MagicMock

from pymongo.read_preferences import ReadPreference

from src.db import async_collections as db_collections


def test_analytics_collections_use_secondary_preferred(monkeypatch) -> None:
    mock_db = MagicMock()

    bookings_coll = MagicMock()
    bookings_with_pref = MagicMock()
    bookings_coll.with_options.return_value = bookings_with_pref

    events_coll = MagicMock()
    events_with_pref = MagicMock()
    events_coll.with_options.return_value = events_with_pref

    users_coll = MagicMock()
    users_with_pref = MagicMock()
    users_coll.with_options.return_value = users_with_pref

    collection_map = {
        "bookings": bookings_coll,
        "events": events_coll,
        "users": users_coll,
    }
    mock_db.__getitem__.side_effect = lambda name: collection_map[name]

    monkeypatch.setattr(db_collections, "get_async_database", lambda: mock_db)

    assert db_collections.async_analytics_bookings_collection() is bookings_with_pref
    assert db_collections.async_analytics_events_collection() is events_with_pref
    assert db_collections.async_analytics_users_collection() is users_with_pref

    bookings_coll.with_options.assert_called_once_with(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )
    events_coll.with_options.assert_called_once_with(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )
    users_coll.with_options.assert_called_once_with(
        read_preference=ReadPreference.SECONDARY_PREFERRED
    )


def test_default_collections_do_not_override_read_preference(monkeypatch) -> None:
    mock_db = MagicMock()

    bookings_coll = MagicMock()
    events_coll = MagicMock()
    users_coll = MagicMock()

    collection_map = {
        "bookings": bookings_coll,
        "events": events_coll,
        "users": users_coll,
    }
    mock_db.__getitem__.side_effect = lambda name: collection_map[name]

    monkeypatch.setattr(db_collections, "get_async_database", lambda: mock_db)

    assert db_collections.async_bookings_collection() is bookings_coll
    assert db_collections.async_events_collection() is events_coll
    assert db_collections.async_users_collection() is users_coll

    bookings_coll.with_options.assert_not_called()
    events_coll.with_options.assert_not_called()
    users_coll.with_options.assert_not_called()
