from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Route, Stop, Schedule, Fare, Alert, RouteStop
from ..schemas import AdminDashboardStats, UserResponse, AdminUserUpdate, AlertResponse
from ..dependencies import require_role

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    total_users = db.query(User).count()
    total_routes = db.query(Route).count()
    total_stops = db.query(Stop).count()
    active_routes = db.query(Route).filter(Route.status == "ACTIVE").count()
    active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()
    total_operators = db.query(User).filter(User.role == "OPERATOR").count()
    total_schedules = db.query(Schedule).count()

    # Route status breakdown
    routes = db.query(Route.status, func.count(Route.id)).group_by(Route.status).all()
    route_status_breakdown = {status: count for status, count in routes}

    # Alert priority breakdown
    alerts = db.query(Alert.priority, func.count(Alert.id)).group_by(Alert.priority).all()
    alert_priority_breakdown = {priority: count for priority, count in alerts}

    # Recent users
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()

    # Recent alerts
    recent_alerts_raw = db.query(Alert).order_by(Alert.created_at.desc()).limit(5).all()
    recent_alerts = []
    for a in recent_alerts_raw:
        route = a.route
        recent_alerts.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "route_id": a.route_id,
            "route_number": route.route_number if route else "All Routes",
            "route_name": route.route_name if route else "System-wide",
            "priority": a.priority,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "status": a.status,
            "created_at": a.created_at
        })

    return {
        "total_users": total_users,
        "total_routes": total_routes,
        "total_stops": total_stops,
        "active_routes": active_routes,
        "active_alerts": active_alerts,
        "total_operators": total_operators,
        "total_schedules": total_schedules,
        "route_status_breakdown": route_status_breakdown,
        "alert_priority_breakdown": alert_priority_breakdown,
        "recent_users": recent_users,
        "recent_alerts": recent_alerts
    }

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    query = db.query(User)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_fmt),
                User.username.ilike(search_fmt),
                User.email.ilike(search_fmt),
                User.phone.ilike(search_fmt)
            )
        )
    if role and role.upper() != "ALL":
        query = query.filter(User.role == role.upper())
    if status and status.upper() != "ALL":
        query = query.filter(User.status == status.upper())

    return query.order_by(User.created_at.desc()).all()

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_status_role(
    user_id: int,
    user_in: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_in.full_name:
        user.full_name = user_in.full_name.strip()
    if user_in.phone is not None:
        user.phone = user_in.phone.strip()
    if user_in.email:
        user.email = user_in.email.strip().lower()
    if user_in.role:
        user.role = user_in.role.upper()
    if user_in.status:
        user.status = user_in.status.upper()

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' deleted successfully."}
