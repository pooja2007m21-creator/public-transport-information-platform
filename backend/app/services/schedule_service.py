from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import Schedule, Route, Stop

class ScheduleService:
    @staticmethod
    def get_schedules(
        db: Session,
        route_id: Optional[int] = None,
        stop_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        query = db.query(Schedule).join(Route, Schedule.route_id == Route.id, isouter=True)
        if route_id:
            query = query.filter(Schedule.route_id == route_id)
        if stop_id:
            query = query.filter(Schedule.stop_id == stop_id)
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                or_(
                    Route.route_number.ilike(search_fmt),
                    Route.route_name.ilike(search_fmt),
                    Schedule.departure_time.ilike(search_fmt),
                    Schedule.status.ilike(search_fmt)
                )
            )
        
        schedules = query.all()
        results = []
        for s in schedules:
            route = s.route
            stop = db.query(Stop).filter(Stop.id == s.stop_id).first() if s.stop_id else None
            results.append({
                "id": s.id,
                "route_id": s.route_id,
                "route_number": route.route_number if route else "N/A",
                "route_name": route.route_name if route else "N/A",
                "stop_id": s.stop_id,
                "stop_name": stop.stop_name if stop else (route.start_point if route else "N/A"),
                "departure_time": s.departure_time,
                "arrival_time": s.arrival_time,
                "frequency": s.frequency,
                "operating_days": s.operating_days,
                "status": s.status
            })
        return results
