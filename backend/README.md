# Public Transport Information Platform - Backend REST API

Built with **Python**, **FastAPI**, **SQLAlchemy ORM**, **Pydantic v2**, and **PyJWT**.

## Features
- **RESTful APIs**: Full CRUD operations for Users, Routes, Stops, Schedules, Fares, Alerts, and Favorites.
- **Journey Planner Engine**: Route discovery matching start and destination locations through stop sequence traversal.
- **Dynamic Fare Calculator**: Stage-based tariff calculation with Student and Senior Citizen concession discounts.
- **RBAC Security**: JWT tokens with roles (`USER`, `OPERATOR`, `ADMIN`) and bcrypt password hashing.
- **Auto-generated Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed database with realistic transit network data
python seed_data.py

# 3. Run FastAPI application
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Demo Credentials
- **Admin**: `admin` / `admin123`
- **Operator**: `operator` / `operator123`
- **User**: `john_doe` / `password123`
