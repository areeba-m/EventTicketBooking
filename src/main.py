import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.db.connection import close_mongo_connection, connect_to_mongo
from src.db.indexes import ensure_indexes
from src.exceptions import InvalidObjectIdError
from src.routes import analytics, auth, bookings, events, users

app = FastAPI(title="Event Ticket Booking")
logger = logging.getLogger("event_ticket_booking")

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


@app.on_event("startup")
def _startup() -> None:
    connect_to_mongo()
    ensure_indexes()


@app.on_event("shutdown")
def _shutdown() -> None:
    close_mongo_connection()


app.include_router(users.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(analytics.router)
