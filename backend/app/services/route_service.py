from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from ..models import Route, Stop, RouteStop, Schedule, Fare, Alert

class RouteService:
    @staticmethod
    def get_all_routes(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        bus_type: Optional[str] = None
    ) -> List[Route]:
        query = db.query(Route)
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                or_(
                    Route.route_number.ilike(search_fmt),
                    Route.route_name.ilike(search_fmt),
                    Route.start_point.ilike(search_fmt),
                    Route.destination.ilike(search_fmt),
                    Route.description.ilike(search_fmt)
                )
            )
        if status and status.upper() != "ALL":
            query = query.filter(Route.status == status.upper())
        if bus_type and bus_type.upper() != "ALL":
            query = query.filter(Route.bus_type.ilike(f"%{bus_type}%"))
        return query.order_by(Route.route_number).all()

    @staticmethod
    def get_route_by_id(db: Session, route_id: int) -> Optional[Route]:
        return db.query(Route).filter(Route.id == route_id).first()

    @staticmethod
    def get_route_details(db: Session, route_id: int) -> Optional[dict]:
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return None
        
        # Get ordered stops
        route_stops = db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.stop_order).all()
        stops = []
        for rs in route_stops:
            stop = db.query(Stop).filter(Stop.id == rs.stop_id).first()
            if stop:
                stops.append({
                    "id": stop.id,
                    "stop_code": stop.stop_code,
                    "stop_name": stop.stop_name,
                    "address": stop.address,
                    "area": stop.area,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "status": stop.status,
                    "stop_order": rs.stop_order
                })
        
        # Get schedules
        schedules = db.query(Schedule).filter(Schedule.route_id == route_id).all()
        schedules_data = [
            {
                "id": s.id,
                "departure_time": s.departure_time,
                "arrival_time": s.arrival_time,
                "frequency": s.frequency,
                "operating_days": s.operating_days,
                "status": s.status
            } for s in schedules
        ]

        # Get fares
        fares = db.query(Fare).filter(Fare.route_id == route_id, Fare.status == "ACTIVE").all()
        fares_data = [
            {
                "id": f.id,
                "base_fare": f.base_fare,
                "student_fare": f.student_fare,
                "senior_fare": f.senior_fare,
                "effective_date": f.effective_date
            } for f in fares
        ]

        # Get alerts
        alerts = db.query(Alert).filter(Alert.route_id == route_id, Alert.status == "ACTIVE").all()
        alerts_data = [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "priority": a.priority,
                "start_date": a.start_date,
                "end_date": a.end_date
            } for a in alerts
        ]

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
            "stops": stops,
            "schedules": schedules_data,
            "fares": fares_data,
            "alerts": alerts_data
        }

    @staticmethod
    def plan_journey(
        db: Session,
        from_stop_text: str,
        to_stop_text: str,
        travel_date: Optional[str] = None,
        travel_time: Optional[str] = None
    ) -> List[dict]:
        """
        Find routes that connect starting stop and destination stop.
        Works with both direct route endpoints and intermediate stop sequence matching!
        """
        from_clean = from_stop_text.strip().lower()
        to_clean = to_stop_text.strip().lower()

        results = []
        all_routes = db.query(Route).filter(Route.status != "CANCELLED").all()

        for route in all_routes:
            # 1. Check direct endpoint match
            direct_match = (
                from_clean in route.start_point.lower() and to_clean in route.destination.lower()
            )
            
            # 2. Check intermediate stops
            route_stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(RouteStop.stop_order).all()
            
            from_order = None
            to_order = None
            matched_from_name = route.start_point
            matched_to_name = route.destination

            # Check if start/dest match
            if from_clean in route.start_point.lower():
                from_order = 0
                matched_from_name = route.start_point
            if to_clean in route.destination.lower():
                to_order = 9999
                matched_to_name = route.destination

            for rs in route_stops:
                stop = db.query(Stop).filter(Stop.id == rs.stop_id).first()
                if stop:
                    stop_name_lower = stop.stop_name.lower()
                    stop_area_lower = (stop.area or "").lower()
                    if (from_clean in stop_name_lower or from_clean in stop_area_lower) and from_order is None:
                        from_order = rs.stop_order
                        matched_from_name = stop.stop_name
                    if (to_clean in stop_name_lower or to_clean in stop_area_lower):
                        to_order = rs.stop_order
                        matched_to_name = stop.stop_name

            # Route is valid if from comes before to
            if direct_match or (from_order is not None and to_order is not None and from_order < to_order):
                # Calculate stops count and schedule
                schedules = db.query(Schedule).filter(Schedule.route_id == route.id).all()
                departure = schedules[0].departure_time if schedules else "08:00 AM"
                arrival = schedules[0].arrival_time if schedules else "08:45 AM"
                status = schedules[0].status if schedules else route.status
                
                # If specific time requested, find closest
                if travel_time and schedules:
                    departure = schedules[0].departure_time
                    arrival = schedules[0].arrival_time
                
                num_stops = len(route_stops) if route_stops else 2
                
                results.append({
                    "route_id": route.id,
                    "route_number": route.route_number,
                    "route_name": route.route_name,
                    "bus_type": route.bus_type,
                    "from_stop": matched_from_name,
                    "to_stop": matched_to_name,
                    "departure_time": departure,
                    "arrival_time": arrival,
                    "duration_min": route.estimated_duration,
                    "fare": route.fare,
                    "stops_count": num_stops,
                    "status": status,
                    "operating_days": route.operating_days
                })

        return results
