import os
from datetime import datetime, timedelta
from app.database import engine, Base, SessionLocal
from app.models import User, Route, Stop, RouteStop, Schedule, Fare, Alert, Favorite, SearchHistory
from app.security import hash_password

def seed_database():
    print("Resetting and creating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Seeding Users...")
        # 1. Users
        users = [
            User(
                full_name="System Administrator",
                username="admin",
                email="admin@transport.gov",
                phone="+91 98765 43210",
                password_hash=hash_password("admin123"),
                role="ADMIN",
                status="ACTIVE"
            ),
            User(
                full_name="Transit Operations Lead",
                username="operator",
                email="operator@transport.gov",
                phone="+91 98765 43211",
                password_hash=hash_password("operator123"),
                role="OPERATOR",
                status="ACTIVE"
            ),
            User(
                full_name="John Doe",
                username="john_doe",
                email="john@example.com",
                phone="+91 98765 11111",
                password_hash=hash_password("password123"),
                role="USER",
                status="ACTIVE"
            ),
            User(
                full_name="Sarah Miller",
                username="sarah_m",
                email="sarah@example.com",
                phone="+91 98765 22222",
                password_hash=hash_password("password123"),
                role="USER",
                status="ACTIVE"
            ),
            User(
                full_name="Rahul Kumar",
                username="rahul_k",
                email="rahul@example.com",
                phone="+91 98765 33333",
                password_hash=hash_password("password123"),
                role="USER",
                status="ACTIVE"
            ),
            User(
                full_name="Anita Sharma",
                username="anita_s",
                email="anita@example.com",
                phone="+91 98765 44444",
                password_hash=hash_password("password123"),
                role="USER",
                status="ACTIVE"
            )
        ]
        db.add_all(users)
        db.commit()

        print("Seeding Stops...")
        # 2. Stops
        stops_data = [
            Stop(id=1, stop_code="CBS-101", stop_name="Central Bus Stand", address="Platform 1-4, Central Terminal", area="Downtown", latitude=18.5204, longitude=73.8567, status="ACTIVE"),
            Stop(id=2, stop_code="MMK-102", stop_name="Main Market", address="Market Circle, Trade Plaza", area="Commercial District", latitude=18.5140, longitude=73.8510, status="ACTIVE"),
            Stop(id=3, stop_code="GHP-103", stop_name="Government Hospital", address="Health Avenue, North Wing", area="Civic Center", latitude=18.5320, longitude=73.8400, status="ACTIVE"),
            Stop(id=4, stop_code="RST-104", stop_name="Railway Station", address="Main Railway Concourse", area="Station Area", latitude=18.5284, longitude=73.8743, status="ACTIVE"),
            Stop(id=5, stop_code="CRD-105", stop_name="College Road / University", address="University Gate 2", area="Academic Zone", latitude=18.5520, longitude=73.8260, status="ACTIVE"),
            Stop(id=6, stop_code="CML-106", stop_name="City Mall", address="Phoenix Gateway Boulevard", area="East End", latitude=18.5360, longitude=73.8930, status="ACTIVE"),
            Stop(id=7, stop_code="TPK-107", stop_name="Tech Park / IT Hub", address="Phase 1 Cyber Corridor", area="Silicon Valley", latitude=18.5910, longitude=73.7380, status="ACTIVE"),
            Stop(id=8, stop_code="APT-108", stop_name="Airport Terminal", address="Departure Gate 3, International Airport", area="Aero City", latitude=18.5820, longitude=73.9190, status="ACTIVE")
        ]
        db.add_all(stops_data)
        db.commit()

        print("Seeding Routes...")
        # 3. Routes
        routes_data = [
            Route(
                id=1,
                route_number="21A",
                route_name="Central - Railway Express",
                start_point="Central Bus Stand",
                destination="Railway Station",
                description="High-frequency urban route linking Central Bus Stand with Railway Station via Main Market and Government Hospital.",
                distance=8.5,
                estimated_duration=30,
                fare=20.0,
                operating_days="Monday - Sunday",
                status="ACTIVE",
                bus_type="Standard Express"
            ),
            Route(
                id=2,
                route_number="42B",
                route_name="Central - IT Hub Fastrack",
                start_point="Central Bus Stand",
                destination="Tech Park / IT Hub",
                description="Direct commuter express route with air-conditioned fleet connecting downtown to the IT tech corridor.",
                distance=18.2,
                estimated_duration=45,
                fare=35.0,
                operating_days="Monday - Saturday",
                status="DELAYED",
                bus_type="AC Express"
            ),
            Route(
                id=3,
                route_number="18C",
                route_name="Railway - Airport Flyer",
                start_point="Railway Station",
                destination="Airport Terminal",
                description="Dedicated eco-friendly electric rapid bus connection from Railway Station to Airport Terminal with luggage racks.",
                distance=12.0,
                estimated_duration=35,
                fare=25.0,
                operating_days="Monday - Sunday",
                status="SUSPENDED",
                bus_type="Electric Rapid"
            ),
            Route(
                id=4,
                route_number="15D",
                route_name="Market - University Feeder",
                start_point="Main Market",
                destination="College Road / University",
                description="Student and faculty commuter route through Government Hospital to University Campus.",
                distance=7.4,
                estimated_duration=25,
                fare=15.0,
                operating_days="Monday - Saturday",
                status="ACTIVE",
                bus_type="Standard Express"
            ),
            Route(
                id=5,
                route_number="7A",
                route_name="City Mall - Central Circular",
                start_point="City Mall",
                destination="Central Bus Stand",
                description="Popular retail and residential connector route linking shopping malls, Railway Station, and Central Stand.",
                distance=10.5,
                estimated_duration=30,
                fare=20.0,
                operating_days="Monday - Sunday",
                status="ACTIVE",
                bus_type="Metro Feeder"
            )
        ]
        db.add_all(routes_data)
        db.commit()

        print("Seeding Route Stops...")
        # 4. Route Stops (Sequences)
        route_stops = [
            # Route 21A: Central -> Main Market -> Govt Hospital -> Railway Station
            RouteStop(route_id=1, stop_id=1, stop_order=1),
            RouteStop(route_id=1, stop_id=2, stop_order=2),
            RouteStop(route_id=1, stop_id=3, stop_order=3),
            RouteStop(route_id=1, stop_id=4, stop_order=4),

            # Route 42B: Central -> Main Market -> College Road -> Tech Park
            RouteStop(route_id=2, stop_id=1, stop_order=1),
            RouteStop(route_id=2, stop_id=2, stop_order=2),
            RouteStop(route_id=2, stop_id=5, stop_order=3),
            RouteStop(route_id=2, stop_id=7, stop_order=4),

            # Route 18C: Railway Station -> City Mall -> Airport Terminal
            RouteStop(route_id=3, stop_id=4, stop_order=1),
            RouteStop(route_id=3, stop_id=6, stop_order=2),
            RouteStop(route_id=3, stop_id=8, stop_order=3),

            # Route 15D: Main Market -> Govt Hospital -> College Road
            RouteStop(route_id=4, stop_id=2, stop_order=1),
            RouteStop(route_id=4, stop_id=3, stop_order=2),
            RouteStop(route_id=4, stop_id=5, stop_order=3),

            # Route 7A: City Mall -> Railway Station -> Main Market -> Central Bus Stand
            RouteStop(route_id=5, stop_id=6, stop_order=1),
            RouteStop(route_id=5, stop_id=4, stop_order=2),
            RouteStop(route_id=5, stop_id=2, stop_order=3),
            RouteStop(route_id=5, stop_id=1, stop_order=4)
        ]
        db.add_all(route_stops)
        db.commit()

        print("Seeding Schedules...")
        # 5. Schedules
        schedules_data = [
            # Route 21A
            Schedule(route_id=1, stop_id=1, departure_time="08:00 AM", arrival_time="08:30 AM", frequency="15 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=1, stop_id=1, departure_time="10:15 AM", arrival_time="10:45 AM", frequency="15 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=1, stop_id=1, departure_time="01:30 PM", arrival_time="02:00 PM", frequency="15 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=1, stop_id=1, departure_time="05:45 PM", arrival_time="06:15 PM", frequency="15 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=1, stop_id=1, departure_time="08:30 PM", arrival_time="09:00 PM", frequency="20 minutes", operating_days="Monday - Sunday", status="ON TIME"),

            # Route 42B
            Schedule(route_id=2, stop_id=1, departure_time="08:15 AM", arrival_time="09:00 AM", frequency="20 minutes", operating_days="Monday - Saturday", status="DELAYED"),
            Schedule(route_id=2, stop_id=1, departure_time="09:30 AM", arrival_time="10:15 AM", frequency="20 minutes", operating_days="Monday - Saturday", status="DELAYED"),
            Schedule(route_id=2, stop_id=1, departure_time="05:15 PM", arrival_time="06:00 PM", frequency="20 minutes", operating_days="Monday - Saturday", status="DELAYED"),
            Schedule(route_id=2, stop_id=1, departure_time="07:00 PM", arrival_time="07:45 PM", frequency="30 minutes", operating_days="Monday - Saturday", status="ON TIME"),

            # Route 18C
            Schedule(route_id=3, stop_id=4, departure_time="06:00 AM", arrival_time="06:35 AM", frequency="30 minutes", operating_days="Monday - Sunday", status="SUSPENDED"),
            Schedule(route_id=3, stop_id=4, departure_time="11:00 AM", arrival_time="11:35 AM", frequency="30 minutes", operating_days="Monday - Sunday", status="SUSPENDED"),
            Schedule(route_id=3, stop_id=4, departure_time="04:30 PM", arrival_time="05:05 PM", frequency="30 minutes", operating_days="Monday - Sunday", status="SUSPENDED"),

            # Route 15D
            Schedule(route_id=4, stop_id=2, departure_time="07:45 AM", arrival_time="08:10 AM", frequency="15 minutes", operating_days="Monday - Saturday", status="ON TIME"),
            Schedule(route_id=4, stop_id=2, departure_time="09:00 AM", arrival_time="09:25 AM", frequency="15 minutes", operating_days="Monday - Saturday", status="ON TIME"),
            Schedule(route_id=4, stop_id=2, departure_time="02:15 PM", arrival_time="02:40 PM", frequency="15 minutes", operating_days="Monday - Saturday", status="ON TIME"),
            Schedule(route_id=4, stop_id=2, departure_time="06:00 PM", arrival_time="06:25 PM", frequency="15 minutes", operating_days="Monday - Saturday", status="ON TIME"),

            # Route 7A
            Schedule(route_id=5, stop_id=6, departure_time="08:30 AM", arrival_time="09:00 AM", frequency="20 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=5, stop_id=6, departure_time="12:00 PM", arrival_time="12:30 PM", frequency="20 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=5, stop_id=6, departure_time="04:45 PM", arrival_time="05:15 PM", frequency="20 minutes", operating_days="Monday - Sunday", status="ON TIME"),
            Schedule(route_id=5, stop_id=6, departure_time="08:15 PM", arrival_time="08:45 PM", frequency="20 minutes", operating_days="Monday - Sunday", status="ON TIME")
        ]
        db.add_all(schedules_data)
        db.commit()

        print("Seeding Fares...")
        # 6. Fares
        fares_data = [
            Fare(route_id=1, base_fare=20.0, student_fare=10.0, senior_fare=12.0, effective_date="2026-01-01", status="ACTIVE"),
            Fare(route_id=2, base_fare=35.0, student_fare=18.0, senior_fare=22.0, effective_date="2026-01-01", status="ACTIVE"),
            Fare(route_id=3, base_fare=25.0, student_fare=15.0, senior_fare=18.0, effective_date="2026-01-01", status="ACTIVE"),
            Fare(route_id=4, base_fare=15.0, student_fare=8.0, senior_fare=10.0, effective_date="2026-01-01", status="ACTIVE"),
            Fare(route_id=5, base_fare=20.0, student_fare=10.0, senior_fare=12.0, effective_date="2026-01-01", status="ACTIVE")
        ]
        db.add_all(fares_data)
        db.commit()

        print("Seeding Service Alerts...")
        # 7. Service Alerts
        alerts_data = [
            Alert(
                title="Route 21A Minor Delays - Road Maintenance",
                description="Route 21A may experience 5-10 minute delays near Government Hospital junction due to ongoing road resurfacing work.",
                route_id=1,
                priority="MEDIUM",
                start_date="2026-10-01",
                end_date="2026-10-10",
                status="ACTIVE"
            ),
            Alert(
                title="Route 42B Tech Corridor Peak Hour Delays",
                description="Heavy traffic on Expressway is causing 15-20 minute delays on Route 42B between 08:30 AM and 10:00 AM.",
                route_id=2,
                priority="HIGH",
                start_date="2026-10-04",
                end_date="2026-10-08",
                status="ACTIVE"
            ),
            Alert(
                title="Route 18C Service Temporarily Suspended",
                description="Route 18C Airport Flyer electric bus service is temporarily suspended due to charging station maintenance at Airport Depot.",
                route_id=3,
                priority="CRITICAL",
                start_date="2026-10-04",
                end_date="2026-10-05",
                status="ACTIVE"
            ),
            Alert(
                title="Additional Buses for Weekend Festival",
                description="Transport authority will operate 25% additional buses on Routes 21A and 7A during the upcoming weekend.",
                route_id=None,
                priority="LOW",
                start_date="2026-10-05",
                end_date="2026-10-12",
                status="ACTIVE"
            )
        ]
        db.add_all(alerts_data)
        db.commit()

        print("Seeding User Favorites & History...")
        # 8. Favorites & History
        favs = [
            Favorite(user_id=3, route_id=1, favorite_type="ROUTE"),
            Favorite(user_id=3, route_id=2, favorite_type="ROUTE"),
            Favorite(user_id=3, stop_id=1, favorite_type="STOP"),
            Favorite(user_id=3, stop_id=4, favorite_type="STOP"),
            Favorite(user_id=4, route_id=4, favorite_type="ROUTE")
        ]
        db.add_all(favs)

        history = [
            SearchHistory(user_id=3, from_stop="Central Bus Stand", to_stop="Railway Station", search_date="2026-10-04", search_time="10:15 AM"),
            SearchHistory(user_id=3, from_stop="Central Bus Stand", to_stop="Tech Park / IT Hub", search_date="2026-10-04", search_time="08:30 AM"),
            SearchHistory(user_id=3, from_stop="Main Market", to_stop="College Road / University", search_date="2026-10-03", search_time="02:00 PM")
        ]
        db.add_all(history)
        db.commit()

        print("Database successfully seeded with comprehensive sample data!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
