from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Fare, Route, Stop, RouteStop

class FareService:
    @staticmethod
    def get_all_fares(db: Session) -> List[dict]:
        fares = db.query(Fare).all()
        results = []
        for f in fares:
            route = db.query(Route).filter(Route.id == f.route_id).first()
            results.append({
                "id": f.id,
                "route_id": f.route_id,
                "route_number": route.route_number if route else "N/A",
                "route_name": route.route_name if route else "N/A",
                "distance": route.distance if route else 0.0,
                "base_fare": f.base_fare,
                "student_fare": f.student_fare,
                "senior_fare": f.senior_fare,
                "effective_date": f.effective_date,
                "status": f.status
            })
        return results

    @staticmethod
    def calculate_fare(
        db: Session,
        from_stop_id: int,
        to_stop_id: int,
        passenger_type: str = "REGULAR"
    ) -> Optional[dict]:
        stop_from = db.query(Stop).filter(Stop.id == from_stop_id).first()
        stop_to = db.query(Stop).filter(Stop.id == to_stop_id).first()

        if not stop_from or not stop_to:
            return None

        # Find common routes
        from_route_ids = [rs.route_id for rs in db.query(RouteStop).filter(RouteStop.stop_id == from_stop_id).all()]
        to_route_ids = [rs.route_id for rs in db.query(RouteStop).filter(RouteStop.stop_id == to_stop_id).all()]
        common_routes = set(from_route_ids).intersection(set(to_route_ids))

        target_route = None
        if common_routes:
            target_route = db.query(Route).filter(Route.id == list(common_routes)[0]).first()
        else:
            # Fallback to nearest active route or first active route
            target_route = db.query(Route).first()

        if not target_route:
            return None

        # Determine stop difference
        rs_from = db.query(RouteStop).filter(RouteStop.route_id == target_route.id, RouteStop.stop_id == from_stop_id).first()
        rs_to = db.query(RouteStop).filter(RouteStop.route_id == target_route.id, RouteStop.stop_id == to_stop_id).first()

        stops_count = abs((rs_to.stop_order if rs_to else 5) - (rs_from.stop_order if rs_from else 1)) + 1
        est_distance = round(stops_count * 2.5, 1)

        fare_record = db.query(Fare).filter(Fare.route_id == target_route.id, Fare.status == "ACTIVE").first()

        if fare_record:
            base = fare_record.base_fare
            student = fare_record.student_fare
            senior = fare_record.senior_fare
        else:
            base = target_route.fare
            student = round(base * 0.5, 2)
            senior = round(base * 0.6, 2)

        # Apply stage multiplier if distance is long
        stage_multiplier = max(1.0, round(stops_count / 3.0, 1))
        
        final_fare = base
        if passenger_type.upper() == "STUDENT":
            final_fare = round(student * (stops_count / 4.0 if stops_count > 4 else 1.0), 2)
        elif passenger_type.upper() == "SENIOR":
            final_fare = round(senior * (stops_count / 4.0 if stops_count > 4 else 1.0), 2)
        else:
            final_fare = round(base * (stops_count / 4.0 if stops_count > 4 else 1.0), 2)

        final_fare = max(10.0, final_fare)

        return {
            "route_id": target_route.id,
            "route_number": target_route.route_number,
            "route_name": target_route.route_name,
            "from_stop": stop_from.stop_name,
            "to_stop": stop_to.stop_name,
            "stops_count": stops_count,
            "distance_km": est_distance,
            "passenger_type": passenger_type.upper(),
            "estimated_fare": float(f"{final_fare:.2f}"),
            "pass_info": "Monthly Pass: ₹800 (Regular) | ₹400 (Student) | Daily All-Route Pass: ₹60"
        }
