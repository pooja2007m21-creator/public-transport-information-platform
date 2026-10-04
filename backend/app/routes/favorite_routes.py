from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Favorite, Route, Stop, SearchHistory, User
from ..schemas import FavoriteCreate, FavoriteResponse, SearchHistoryResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

@router.get("", response_model=List[dict])
def get_user_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    favs = db.query(Favorite).filter(Favorite.user_id == current_user.id).order_by(Favorite.created_at.desc()).all()
    results = []
    for f in favs:
        route_data = None
        stop_data = None
        if f.route_id:
            r = db.query(Route).filter(Route.id == f.route_id).first()
            if r:
                route_data = {
                    "id": r.id,
                    "route_number": r.route_number,
                    "route_name": r.route_name,
                    "start_point": r.start_point,
                    "destination": r.destination,
                    "fare": r.fare,
                    "status": r.status,
                    "bus_type": r.bus_type
                }
        if f.stop_id:
            s = db.query(Stop).filter(Stop.id == f.stop_id).first()
            if s:
                stop_data = {
                    "id": s.id,
                    "stop_code": s.stop_code,
                    "stop_name": s.stop_name,
                    "area": s.area,
                    "status": s.status
                }
        results.append({
            "id": f.id,
            "user_id": f.user_id,
            "favorite_type": f.favorite_type,
            "route_id": f.route_id,
            "stop_id": f.stop_id,
            "created_at": f.created_at,
            "route": route_data,
            "stop": stop_data
        })
    return results

@router.post("", status_code=status.HTTP_201_CREATED)
def add_favorite(
    fav_in: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if fav_in.favorite_type == "ROUTE" and not fav_in.route_id:
        raise HTTPException(status_code=400, detail="route_id is required for route favorite.")
    if fav_in.favorite_type == "STOP" and not fav_in.stop_id:
        raise HTTPException(status_code=400, detail="stop_id is required for stop favorite.")

    # Check for duplicate
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.favorite_type == fav_in.favorite_type,
        Favorite.route_id == fav_in.route_id if fav_in.route_id else Favorite.route_id.is_(None),
        Favorite.stop_id == fav_in.stop_id if fav_in.stop_id else Favorite.stop_id.is_(None)
    ).first()

    if existing:
        return {"message": "Already in favorites", "id": existing.id}

    new_fav = Favorite(
        user_id=current_user.id,
        route_id=fav_in.route_id,
        stop_id=fav_in.stop_id,
        favorite_type=fav_in.favorite_type.upper()
    )
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return {"message": "Added to favorites successfully.", "id": new_fav.id}

@router.delete("/{fav_id}")
def remove_favorite(
    fav_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fav = db.query(Favorite).filter(Favorite.id == fav_id, Favorite.user_id == current_user.id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite item not found.")
    
    db.delete(fav)
    db.commit()
    return {"message": "Favorite removed successfully."}

@router.delete("/route/{route_id}")
def remove_favorite_by_route(
    route_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fav = db.query(Favorite).filter(Favorite.route_id == route_id, Favorite.user_id == current_user.id).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"message": "Removed from favorites."}

@router.delete("/stop/{stop_id}")
def remove_favorite_by_stop(
    stop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fav = db.query(Favorite).filter(Favorite.stop_id == stop_id, Favorite.user_id == current_user.id).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"message": "Removed from favorites."}
