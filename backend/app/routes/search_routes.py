from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import SearchHistory, Stop, Route, User
from ..schemas import SearchRequest, JourneyMatchResponse, SearchHistoryResponse, StopResponse
from ..services.route_service import RouteService
from ..dependencies import get_optional_user, get_current_user

router = APIRouter(prefix="/api/search", tags=["Search & Journey Planning"])

@router.post("/routes", response_model=List[JourneyMatchResponse])
def search_journey(
    req: SearchRequest,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_user)
):
    if not req.from_stop or not req.to_stop:
        raise HTTPException(status_code=400, detail="Both starting location and destination are required.")

    # Record search history if user is logged in
    if optional_user:
        history = SearchHistory(
            user_id=optional_user.id,
            from_stop=req.from_stop.strip(),
            to_stop=req.to_stop.strip(),
            search_date=req.travel_date or datetime.utcnow().strftime("%Y-%m-%d"),
            search_time=req.travel_time or datetime.utcnow().strftime("%I:%M %p")
        )
        db.add(history)
        db.commit()

    results = RouteService.plan_journey(
        db,
        from_stop_text=req.from_stop,
        to_stop_text=req.to_stop,
        travel_date=req.travel_date,
        travel_time=req.travel_time
    )
    return results

@router.get("/stops", response_model=List[StopResponse])
def search_stops(
    q: str = Query(..., min_length=1, description="Query string for stop name or area"),
    db: Session = Depends(get_db)
):
    search_fmt = f"%{q.strip()}%"
    stops = db.query(Stop).filter(
        (Stop.stop_name.ilike(search_fmt)) | (Stop.area.ilike(search_fmt)) | (Stop.stop_code.ilike(search_fmt))
    ).limit(20).all()
    return stops

@router.get("/history", response_model=List[SearchHistoryResponse])
def get_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.created_at.desc()).limit(20).all()
    return history

@router.delete("/history")
def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Search history cleared successfully."}
