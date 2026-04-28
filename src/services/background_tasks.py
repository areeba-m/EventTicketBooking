import asyncio
import logging

logger = logging.getLogger("event_ticket_booking")


async def send_booking_confirmation(
    booking_id: str,
    user_id: str,
    event_id: str,
    seats: int,
) -> None:
    """Simulate async notification task with logging."""
    logger.info("Background task: Starting notification for booking %s", booking_id)
    await asyncio.sleep(2)
    logger.info(
        "Background task: Booking %s confirmed for user %s (event: %s, seats: %d)",
        booking_id,
        user_id,
        event_id,
        seats,
    )


async def send_booking_cancellation(
    booking_id: str,
    user_id: str,
    seats: int,
) -> None:
    """Simulate async cancellation notification with logging."""
    logger.info("Background task: Starting cancellation notification for booking %s", booking_id)
    await asyncio.sleep(1)
    logger.info(
        "Background task: Booking %s cancelled for user %s (%d seats restored)",
        booking_id,
        user_id,
        seats,
    )
