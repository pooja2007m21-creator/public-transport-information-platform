from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Schedule, Route, Stop
from ..schemas import ScheduleResponse, ScheduleCreate, ScheduleUpdate
from ..services.schedule_service import ScheduleService
from ..dependencies import require_role

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

@router.get("", response_model=List[ScheduleResponse])
def get_schedules(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    stop_id: Optional[int] = Query(None, description="Filter by stop ID"),
    search: Optional[str] = Query(None, description="Search route or time"),
    db: Session = Depends(get_db)
):
    return ScheduleService.get_schedules(db, route_id=route_id, stop_id=stop_id, search=search)

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    route = schedule.route
    stop = db.query(Stop).filter(Stop.id == schedule.stop_id).first() if schedule.stop_id else None
    return {
        "id": schedule.id,
        "route_id": schedule.route_id,
        "route_number": route.route_number if route else "N/A",
        "route_name": route.route_name if route else "N/A",
        "stop_id": schedule.stop_id,
        "stop_name": stop.stop_name if stop else (route.start_point if route else "N/A"),
        "departure_time": schedule.departure_time,
        "arrival_time": schedule.arrival_time,
        "frequency": schedule.frequency,
        "operating_days": schedule.operating_days,
        "status": schedule.status
    }

@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    sched_in: ScheduleCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    route = db.query(Route).filter(Route.id == sched_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    new_schedule = Schedule(
        route_id=sched_in.route_id,
        stop_id=sched_in.stop_id,
        departure_time=sched_in.departure_time.strip(),
        arrival_time=sched_in.arrival_time.strip(),
        frequency=sched_in.frequency,
        operating_days=sched_in.operating_days,
        status=sched_in.status.upper() if sched_in.status else "ON TIME"
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    stop = db.query(Stop).filter(Stop.id == new_schedule.stop_id).first() if new_schedule.stop_id else None
    return {
        "id": new_schedule.id,
        "route_id": new_schedule.route_id,
        "route_number": route.route_number,
        "route_name": route.route_name,
        "stop_id": new_schedule.stop_id,
        "stop_name": stop.stop_name if stop else route.start_point,
        "departure_time": new_schedule.departure_time,
        "arrival_time": new_schedule.arrival_time,
        "frequency": new_schedule.frequency,
        "operating_days": new_schedule.operating_days,
        "status": new_schedule.status
    }

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    sched_in: ScheduleUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    if sched_in.route_id is not None:
        schedule.route_id = sched_in.route_id
    if sched_in.stop_id is not None:
        schedule.stop_id = sched_in.stop_id
    if sched_in.departure_time is not None:
        schedule.departure_time = sched_in.departure_time.strip()
    if sched_in.arrival_time is not None:
        schedule.arrival_time = sched_in.arrival_time.strip()
    if sched_in.frequency is not None:
        schedule.frequency = sched_in.frequency
    if sched_in.operating_days is not None:
        schedule.operating_days = sched_in.operating_days
    if sched_in.status is not None:
        schedule.status = sched_in.status.upper()

    db.commit()
    db.refresh(schedule)

    route = schedule.route
    stop = db.query(Stop).filter(Stop.id == schedule.stop_id).first() if schedule.stop_id else None
    return {
        "id": schedule.id,
        "route_id": schedule.route_id,
        "route_number": route.route_number if route else "N/A",
        "route_name": route.route_name if route else "N/A",
        "stop_id": schedule.stop_id,
        "stop_name": stop.stop_name if stop else (route.start_point if route else "N/A"),
        "departure_time": schedule.departure_time,
        "arrival_time": schedule.arrival_time,
        "frequency": schedule.frequency,
        "operating_days": schedule.operating_days,
        "status": schedule.status
    }

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully."}
