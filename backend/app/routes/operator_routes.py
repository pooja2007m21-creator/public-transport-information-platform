from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Route, Alert, Schedule, User
from ..schemas import OperatorStatusUpdate, RouteResponse, AlertResponse
from ..dependencies import require_role

router = APIRouter(prefix="/api/operator", tags=["Operator Operations"])

@router.get("/routes", response_model=List[RouteResponse])
def get_operator_routes(
    db: Session = Depends(get_db),
    operator_user: User = Depends(require_role(["OPERATOR", "ADMIN"]))
):
    routes = db.query(Route).all()
    results = []
    for r in routes:
        results.append({
            "id": r.id,
            "route_number": r.route_number,
            "route_name": r.route_name,
            "start_point": r.start_point,
            "destination": r.destination,
            "description": r.description,
            "distance": r.distance,
            "estimated_duration": r.estimated_duration,
            "fare": r.fare,
            "operating_days": r.operating_days,
            "status": r.status,
            "bus_type": r.bus_type,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "stops_count": len(r.route_stops)
        })
    return results

@router.post("/update-status")
def update_route_status(
    status_in: OperatorStatusUpdate,
    db: Session = Depends(get_db),
    operator_user: User = Depends(require_role(["OPERATOR", "ADMIN"]))
):
    route = db.query(Route).filter(Route.id == status_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    new_status = status_in.status.upper()
    route.status = new_status
    route.updated_at = datetime.utcnow()

    # Update related schedules status
    db.query(Schedule).filter(Schedule.route_id == route.id).update({"status": new_status})

    # If alert description or title provided, create an automatic alert
    if status_in.alert_title and status_in.alert_description:
        new_alert = Alert(
            title=status_in.alert_title.strip(),
            description=status_in.alert_description.strip(),
            route_id=route.id,
            priority=status_in.priority.upper() if status_in.priority else "HIGH",
            start_date=datetime.utcnow().strftime("%Y-%m-%d"),
            end_date=datetime.utcnow().strftime("%Y-%m-%d"),
            status="ACTIVE"
        )
        db.add(new_alert)

    db.commit()
    db.refresh(route)
    return {
        "message": f"Status for route {route.route_number} updated to {route.status}.",
        "route_id": route.id,
        "status": route.status
    }
