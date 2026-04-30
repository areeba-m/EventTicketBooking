# Event Ticket Booking

A FastAPI application for managing users, events, bookings, and analytics backed by MongoDB.

## Features

- User registration and login with JWT authentication
- Event creation, listing, updating, and deletion
- Booking creation, listing, and cancellation
- Organizer analytics for bookings and revenue

## Requirements

- Python 3.11+
- MongoDB

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure environment variables in a `.env` file:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=event_ticket_booking
JWT_SECRET=change-me
JWT_ALG=HS256
JWT_EXP_MINUTES=30
```

## Run the app

```bash
uvicorn src.main:app --reload
```

## Tests

```bash
pytest -q
```

## API

- `/auth` - authentication
- `/users` - user profile endpoints
- `/events` - event endpoints
- `/bookings` - booking endpoints
- `/analytics` - organizer analytics
