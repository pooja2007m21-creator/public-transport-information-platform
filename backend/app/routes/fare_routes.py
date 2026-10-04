from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Fare, Route
from ..schemas import FareResponse, FareCreate, FareUpdate, FareCalculateRequest, FareCalculateResponse
from ..services.fare_service import FareService
from ..dependencies import require_role

router = APIRouter(prefix="/api/fares", tags=["Fares"])

@router.get("", response_model=List[FareResponse])
def get_fares(db: Session = Depends(get_db)):
    return FareService.get_all_fares(db)

@router.post("/calculate", response_model=FareCalculateResponse)
def calculate_fare(calc_req: FareCalculateRequest, db: Session = Depends(get_db)):
    result = FareService.calculate_fare(
        db,
        from_stop_id=calc_req.from_stop_id,
        to_stop_id=calc_req.to_stop_id,
        passenger_type=calc_req.passenger_type or "REGULAR"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Could not calculate fare. Please select valid stops.")
    return result

@router.get("/{fare_id}", response_model=FareResponse)
def get_fare(fare_id: int, db: Session = Depends(get_db)):
    fare = db.query(Fare).filter(Fare.id == fare_id).first()
    if not fare:
        raise HTTPException(status_code=404, detail="Fare record not found.")
    route = fare.route
    return {
        "id": fare.id,
        "route_id": fare.route_id,
        "route_number": route.route_number if route else "N/A",
        "route_name": route.route_name if route else "N/A",
        "distance": route.distance if route else 0.0,
        "base_fare": fare.base_fare,
        "student_fare": fare.student_fare,
        "senior_fare": fare.senior_fare,
        "effective_date": fare.effective_date,
        "status": fare.status
    }

@router.post("", response_model=FareResponse, status_code=status.HTTP_201_CREATED)
def create_fare(
    fare_in: FareCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    route = db.query(Route).filter(Route.id == fare_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    new_fare = Fare(
        route_id=fare_in.route_id,
        base_fare=fare_in.base_fare,
        student_fare=fare_in.student_fare,
        senior_fare=fare_in.senior_fare,
        effective_date=fare_in.effective_date,
        status=fare_in.status.upper() if fare_in.status else "ACTIVE"
    )
    db.add(new_fare)
    db.commit()
    db.refresh(new_fare)

    return {
        "id": new_fare.id,
        "route_id": new_fare.route_id,
        "route_number": route.route_number,
        "route_name": route.route_name,
        "distance": route.distance,
        "base_fare": new_fare.base_fare,
        "student_fare": new_fare.student_fare,
        "senior_fare": new_fare.senior_fare,
        "effective_date": new_fare.effective_date,
        "status": new_fare.status
    }

@router.put("/{fare_id}", response_model=FareResponse)
def update_fare(
    fare_id: int,
    fare_in: FareUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    fare = db.query(Fare).filter(Fare.id == fare_id).first()
    if not fare:
        raise HTTPException(status_code=404, detail="Fare record not found.")

    if fare_in.route_id is not None:
        fare.route_id = fare_in.route_id
    if fare_in.base_fare is not None:
        fare.base_fare = fare_in.base_fare
    if fare_in.student_fare is not None:
        fare.student_fare = fare_in.student_fare
    if fare_in.senior_fare is not None:
        fare.senior_fare = fare_in.senior_fare
    if fare_in.effective_date is not None:
        fare.effective_date = fare_in.effective_date
    if fare_in.status is not None:
        fare.status = fare_in.status.upper()

    db.commit()
    db.refresh(fare)

    route = fare.route
    return {
        "id": fare.id,
        "route_id": fare.route_id,
        "route_number": route.route_number if route else "N/A",
        "route_name": route.route_name if route else "N/A",
        "distance": route.distance if route else 0.0,
        "base_fare": fare.base_fare,
        "student_fare": fare.student_fare,
        "senior_fare": fare.senior_fare,
        "effective_date": fare.effective_date,
        "status": fare.status
    }

@router.delete("/{fare_id}")
def delete_fare(
    fare_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["ADMIN"]))
):
    fare = db.query(Fare).filter(Fare.id == fare_id).first()
    if not fare:
        raise HTTPException(status_code=404, detail="Fare record not found.")
    
    db.delete(fare)
    db.commit()
    return {"message": "Fare record deleted successfully."}
