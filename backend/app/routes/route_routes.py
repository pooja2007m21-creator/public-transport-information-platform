from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Route, RouteStop, Stop
from ..schemas import RouteResponse, RouteDetailResponse, RouteCreate, RouteUpdate
from ..services.route_service import RouteService
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/routes", tags=["Routes"])

@router.get("", response_model=List[RouteResponse])
def get_routes(
    search: Optional[str] = Query(None, description="Search route number, name, or endpoints"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, DELAYED, etc.)"),
    bus_type: Optional[str] = Query(None, description="Filter by bus type"),
    db: Session = Depends(get_db)
):
    routes = RouteService.get_all_routes(db, search=search, status=status, bus_type=bus_type)
    results = []
    for r in routes:
        stops_count = db.query(RouteStop).filter(RouteStop.route_id == r.id).count()
        r_dict = {
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
            "stops_count": stops_count
        }
        results.append(r_dict)
    return results

@router.get("/{route_id}", response_model=RouteDetailResponse)
def get_route_details(route_id: int, db: Session = Depends(get_db)):
    details = RouteService.get_route_details(db, route_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Route with ID {route_id} not found.")
    return details

@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route_in: RouteCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    existing = db.query(Route).filter(Route.route_number == route_in.route_number.strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Route number '{route_in.route_number}' already exists.")

    new_route = Route(
        route_number=route_in.route_number.strip().upper(),
        route_name=route_in.route_name.strip(),
        start_point=route_in.start_point.strip(),
        destination=route_in.destination.strip(),
        description=route_in.description,
        distance=route_in.distance,
        estimated_duration=route_in.estimated_duration,
        fare=route_in.fare,
        operating_days=route_in.operating_days,
        status=route_in.status.upper(),
        bus_type=route_in.bus_type
    )
    db.add(new_route)
    db.commit()
    db.refresh(new_route)

    # Attach stop ids if provided
    if route_in.stop_ids:
        for idx, s_id in enumerate(route_in.stop_ids):
            rs = RouteStop(route_id=new_route.id, stop_id=s_id, stop_order=idx + 1)
            db.add(rs)
        db.commit()

    return {
        "id": new_route.id,
        "route_number": new_route.route_number,
        "route_name": new_route.route_name,
        "start_point": new_route.start_point,
        "destination": new_route.destination,
        "description": new_route.description,
        "distance": new_route.distance,
        "estimated_duration": new_route.estimated_duration,
        "fare": new_route.fare,
        "operating_days": new_route.operating_days,
        "status": new_route.status,
        "bus_type": new_route.bus_type,
        "created_at": new_route.created_at,
        "updated_at": new_route.updated_at,
        "stops_count": len(route_in.stop_ids or [])
    }

@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: int,
    route_in: RouteUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN", "OPERATOR"]))
):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    if route_in.route_number and route_in.route_number != route.route_number:
        existing = db.query(Route).filter(Route.route_number == route_in.route_number.strip(), Route.id != route_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Route number already in use.")
        route.route_number = route_in.route_number.strip().upper()

    if route_in.route_name is not None:
        route.route_name = route_in.route_name.strip()
    if route_in.start_point is not None:
        route.start_point = route_in.start_point.strip()
    if route_in.destination is not None:
        route.destination = route_in.destination.strip()
    if route_in.description is not None:
        route.description = route_in.description
    if route_in.distance is not None:
        route.distance = route_in.distance
    if route_in.estimated_duration is not None:
        route.estimated_duration = route_in.estimated_duration
    if route_in.fare is not None:
        route.fare = route_in.fare
    if route_in.operating_days is not None:
        route.operating_days = route_in.operating_days
    if route_in.status is not None:
        route.status = route_in.status.upper()
    if route_in.bus_type is not None:
        route.bus_type = route_in.bus_type

    if route_in.stop_ids is not None:
        db.query(RouteStop).filter(RouteStop.route_id == route.id).delete()
        for idx, s_id in enumerate(route_in.stop_ids):
            rs = RouteStop(route_id=route.id, stop_id=s_id, stop_order=idx + 1)
            db.add(rs)

    route.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(route)

    stops_count = db.query(RouteStop).filter(RouteStop.route_id == route.id).count()
    return {
        "id": route.id,
        "route_number": route.route_number,
        "route_name": route.route_name,
        "start_point": route.start_point,
        "destination": route.destination,
        "description": route.description,
        "distance": route.distance,
        "estimated_duration": route.estimated_duration,
        "fare": route.fare,
        "operating_days": route.operating_days,
        "status": route.status,
        "bus_type": route.bus_type,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
        "stops_count": stops_count
    }

@router.delete("/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")
    
    db.delete(route)
    db.commit()
    return {"message": f"Route '{route.route_number}' deleted successfully."}
