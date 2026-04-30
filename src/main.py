import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.db.async_connection import close_mongo_connection_async, connect_to_mongo_async
from src.db.connection import close_mongo_connection, connect_to_mongo
from src.db.indexes import ensure_indexes
from src.exceptions import InvalidObjectIdError
from src.routes import analytics, auth, bookings, events, users

logger = logging.getLogger("event_ticket_booking")


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    await connect_to_mongo_async()
    ensure_indexes()
    try:
        yield
    finally:
        await close_mongo_connection_async()
        close_mongo_connection()


app = FastAPI(title="Event Ticket Booking", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
    return response


@app.exception_handler(InvalidObjectIdError)
async def invalid_object_id_handler(request: Request, exc: InvalidObjectIdError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(users.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(analytics.router)
