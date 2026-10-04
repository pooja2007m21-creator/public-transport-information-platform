from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Alert, Route
from ..schemas import AlertResponse, AlertCreate, AlertUpdate
from ..services.alert_service import AlertService
from ..dependencies import require_role

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    status: Optional[str] = Query(None, description="ACTIVE, RESOLVED, EXPIRED"),
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    route_id: Optional[int] = Query(None, description="Filter by affected route"),
    search: Optional[str] = Query(None, description="Search keyword"),
    db: Session = Depends(get_db)
):
    return AlertService.get_alerts(db, status=status, priority=priority, route_id=route_id, search=search)

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Service alert not found.")
    route = alert.route
    return {
        "id": alert.id,
        "title": alert.title,
        "description": alert.description,
        "route_id": alert.route_id,
        "route_number": route.route_number if route else "All Routes",
        "route_name": route.route_name if route else "System-wide",
        "priority": alert.priority,
        "start_date": alert.start_date,
        "end_date": alert.end_date,
        "status": alert.status,
        "created_at": alert.created_at
    }

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_in: AlertCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    new_alert = Alert(
        title=alert_in.title.strip(),
        description=alert_in.description.strip(),
        route_id=alert_in.route_id,
        priority=alert_in.priority.upper() if alert_in.priority else "MEDIUM",
        start_date=alert_in.start_date,
        end_date=alert_in.end_date,
        status=alert_in.status.upper() if alert_in.status else "ACTIVE"
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    route = new_alert.route
    return {
        "id": new_alert.id,
        "title": new_alert.title,
        "description": new_alert.description,
        "route_id": new_alert.route_id,
        "route_number": route.route_number if route else "All Routes",
        "route_name": route.route_name if route else "System-wide",
        "priority": new_alert.priority,
        "start_date": new_alert.start_date,
        "end_date": new_alert.end_date,
        "status": new_alert.status,
        "created_at": new_alert.created_at
    }

@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    if alert_in.title is not None:
        alert.title = alert_in.title.strip()
    if alert_in.description is not None:
        alert.description = alert_in.description.strip()
    if alert_in.route_id is not None:
        alert.route_id = alert_in.route_id if alert_in.route_id != 0 else None
    if alert_in.priority is not None:
        alert.priority = alert_in.priority.upper()
    if alert_in.start_date is not None:
        alert.start_date = alert_in.start_date
    if alert_in.end_date is not None:
        alert.end_date = alert_in.end_date
    if alert_in.status is not None:
        alert.status = alert_in.status.upper()

    db.commit()
    db.refresh(alert)

    route = alert.route
    return {
        "id": alert.id,
        "title": alert.title,
        "description": alert.description,
        "route_id": alert.route_id,
        "route_number": route.route_number if route else "All Routes",
        "route_name": route.route_name if route else "System-wide",
        "priority": alert.priority,
        "start_date": alert.start_date,
        "end_date": alert.end_date,
        "status": alert.status,
        "created_at": alert.created_at
    }

@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    db.delete(alert)
    db.commit()
    return {"message": "Service alert deleted successfully."}
