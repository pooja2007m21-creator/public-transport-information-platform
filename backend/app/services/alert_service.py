from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import Alert, Route

class AlertService:
    @staticmethod
    def get_alerts(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        route_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        query = db.query(Alert).join(Route, Alert.route_id == Route.id, isouter=True)
        
        if status and status.upper() != "ALL":
            query = query.filter(Alert.status == status.upper())
        if priority and priority.upper() != "ALL":
            query = query.filter(Alert.priority == priority.upper())
        if route_id:
            query = query.filter(Alert.route_id == route_id)
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                or_(
                    Alert.title.ilike(search_fmt),
                    Alert.description.ilike(search_fmt),
                    Route.route_number.ilike(search_fmt)
                )
            )

        alerts = query.order_by(Alert.created_at.desc()).all()
        results = []
        for a in alerts:
            route = a.route
            results.append({
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
        return results
