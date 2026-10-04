import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Favorite, SearchHistory, Alert, Route, Stop, User
from .dependencies import get_current_user
from .schemas import UserDashboardStats, AlertResponse, SearchHistoryResponse
from .routes import (
    auth_routes,
    user_routes,
    route_routes,
    stop_routes,
    schedule_routes,
    fare_routes,
    alert_routes,
    favorite_routes,
    search_routes,
    admin_routes,
    operator_routes
)

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Public Transport Information Platform API",
    description="Full-stack REST API for passenger information, route navigation, schedules, fares, service status, and admin/operator management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend local development & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(route_routes.router)
app.include_router(stop_routes.router)
app.include_router(schedule_routes.router)
app.include_router(fare_routes.router)
app.include_router(alert_routes.router)
app.include_router(favorite_routes.router)
app.include_router(search_routes.router)
app.include_router(admin_routes.router)
app.include_router(operator_routes.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Public Transport Information Platform",
        "version": "1.0.0"
    }

@app.get("/api/dashboard/user", response_model=UserDashboardStats, tags=["Dashboard"])
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch user favorites
    fav_routes = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.favorite_type == "ROUTE").all()
    fav_routes_data = []
    for f in fav_routes:
        if f.route:
            fav_routes_data.append({
                "id": f.id,
                "route_id": f.route.id,
                "route_number": f.route.route_number,
                "route_name": f.route.route_name,
                "start_point": f.route.start_point,
                "destination": f.route.destination,
                "fare": f.route.fare,
                "status": f.route.status,
                "bus_type": f.route.bus_type
            })

    fav_stops = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.favorite_type == "STOP").all()
    fav_stops_data = []
    for f in fav_stops:
        if f.stop:
            fav_stops_data.append({
                "id": f.id,
                "stop_id": f.stop.id,
                "stop_code": f.stop.stop_code,
                "stop_name": f.stop.stop_name,
                "area": f.stop.area,
                "status": f.stop.status
            })

    # Recent searches
    recent_searches = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).order_by(SearchHistory.created_at.desc()).limit(5).all()

    # Active alerts
    active_alerts_raw = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(Alert.created_at.desc()).limit(5).all()
    active_alerts = []
    for a in active_alerts_raw:
        r = a.route
        active_alerts.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "route_id": a.route_id,
            "route_number": r.route_number if r else "All Routes",
            "route_name": r.route_name if r else "System-wide",
            "priority": a.priority,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "status": a.status,
            "created_at": a.created_at
        })

    return {
        "user_name": current_user.full_name,
        "total_favorites": len(fav_routes_data),
        "total_saved_stops": len(fav_stops_data),
        "recent_searches_count": len(recent_searches),
        "active_alerts_count": len(active_alerts),
        "recent_searches": recent_searches,
        "favorite_routes": fav_routes_data,
        "saved_stops": fav_stops_data,
        "active_alerts": active_alerts
    }

# Mount static frontend files if directory exists
# __file__ is in backend/app/main.py -> parent of parent is backend -> parent of backend is project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
