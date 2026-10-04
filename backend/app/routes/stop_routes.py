from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..database import get_db
from ..models import Stop, RouteStop, Route, Schedule
from ..schemas import StopResponse, StopDetailResponse, StopCreate, StopUpdate
from ..dependencies import require_role

router = APIRouter(prefix="/api/stops", tags=["Stops"])

@router.get("", response_model=List[StopResponse])
def get_stops(
    search: Optional[str] = Query(None, description="Search stop name, code, or area"),
    status: Optional[str] = Query(None, description="Status filter"),
    db: Session = Depends(get_db)
):
    query = db.query(Stop)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Stop.stop_name.ilike(search_fmt),
                Stop.stop_code.ilike(search_fmt),
                Stop.area.ilike(search_fmt),
                Stop.address.ilike(search_fmt)
            )
        )
    if status and status.upper() != "ALL":
        query = query.filter(Stop.status == status.upper())
    return query.order_by(Stop.stop_name).all()

@router.get("/{stop_id}", response_model=StopDetailResponse)
def get_stop_details(stop_id: int, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found.")

    # Find passing routes
    route_stops = db.query(RouteStop).filter(RouteStop.stop_id == stop_id).all()
    passing_routes = []
    upcoming_buses = []

    for rs in route_stops:
        route = db.query(Route).filter(Route.id == rs.route_id).first()
        if route:
            passing_routes.append({
                "route_id": route.id,
                "route_number": route.route_number,
                "route_name": route.route_name,
                "start_point": route.start_point,
                "destination": route.destination,
                "status": route.status,
                "bus_type": route.bus_type
            })
            
            # Fetch schedules for this route
            schedules = db.query(Schedule).filter(Schedule.route_id == route.id).all()
            for s in schedules:
                upcoming_buses.append({
                    "route_number": route.route_number,
                    "route_name": route.route_name,
                    "departure_time": s.departure_time,
                    "arrival_time": s.arrival_time,
                    "status": s.status,
                    "frequency": s.frequency
                })

    return {
        "id": stop.id,
        "stop_code": stop.stop_code,
        "stop_name": stop.stop_name,
        "address": stop.address,
        "area": stop.area,
        "latitude": stop.latitude,
        "longitude": stop.longitude,
        "status": stop.status,
        "passing_routes": passing_routes,
        "upcoming_buses": upcoming_buses
    }

@router.post("", response_model=StopResponse, status_code=status.HTTP_201_CREATED)
def create_stop(
    stop_in: StopCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    existing = db.query(Stop).filter(Stop.stop_code == stop_in.stop_code.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Stop code '{stop_in.stop_code}' already exists.")

    new_stop = Stop(
        stop_code=stop_in.stop_code.strip().upper(),
        stop_name=stop_in.stop_name.strip(),
        address=stop_in.address,
        area=stop_in.area,
        latitude=stop_in.latitude,
        longitude=stop_in.longitude,
        status=stop_in.status.upper() if stop_in.status else "ACTIVE"
    )
    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)
    return new_stop

@router.put("/{stop_id}", response_model=StopResponse)
def update_stop(
    stop_id: int,
    stop_in: StopUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found.")

    if stop_in.stop_code and stop_in.stop_code != stop.stop_code:
        existing = db.query(Stop).filter(Stop.stop_code == stop_in.stop_code.strip().upper(), Stop.id != stop_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Stop code already in use.")
        stop.stop_code = stop_in.stop_code.strip().upper()

    if stop_in.stop_name is not None:
        stop.stop_name = stop_in.stop_name.strip()
    if stop_in.address is not None:
        stop.address = stop_in.address
    if stop_in.area is not None:
        stop.area = stop_in.area
    if stop_in.latitude is not None:
        stop.latitude = stop_in.latitude
    if stop_in.longitude is not None:
        stop.longitude = stop_in.longitude
    if stop_in.status is not None:
        stop.status = stop_in.status.upper()

    db.commit()
    db.refresh(stop)
    return stop

@router.delete("/{stop_id}")
def delete_stop(
    stop_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found.")
    
    db.delete(stop)
    db.commit()
    return {"message": f"Stop '{stop.stop_name}' deleted successfully."}
