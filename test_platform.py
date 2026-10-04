import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("Testing Backend APIs...")

    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[OK] Health Check Passed:", res.json())

    # 2. Public Routes
    res = requests.get(f"{BASE_URL}/api/routes")
    assert res.status_code == 200
    routes = res.json()
    assert len(routes) >= 5
    print(f"[OK] Routes API: Found {len(routes)} routes")

    # 3. Public Stops
    res = requests.get(f"{BASE_URL}/api/stops")
    assert res.status_code == 200
    stops = res.json()
    assert len(stops) >= 8
    print(f"[OK] Stops API: Found {len(stops)} stops")

    # 4. Route Details
    res = requests.get(f"{BASE_URL}/api/routes/1")
    assert res.status_code == 200
    rd = res.json()
    assert len(rd["stops"]) > 0
    print(f"[OK] Route Details API: Route {rd['route_number']} has {len(rd['stops'])} ordered stops")

    # 5. Stop Details with upcoming buses
    res = requests.get(f"{BASE_URL}/api/stops/1")
    assert res.status_code == 200
    sd = res.json()
    assert len(sd["upcoming_buses"]) > 0
    print(f"[OK] Stop Details API: Stop '{sd['stop_name']}' has {len(sd['upcoming_buses'])} upcoming buses")

    # 6. Journey Search Planner
    res = requests.post(f"{BASE_URL}/api/search/routes", json={
        "from_stop": "Central Bus Stand",
        "to_stop": "Railway Station"
    })
    assert res.status_code == 200
    matches = res.json()
    assert len(matches) > 0
    print(f"[OK] Journey Planner API: Found {len(matches)} matching route(s)")

    # 7. Fare Calculation
    res = requests.post(f"{BASE_URL}/api/fares/calculate", json={
        "from_stop_id": 1,
        "to_stop_id": 4,
        "passenger_type": "REGULAR"
    })
    assert res.status_code == 200
    fare_res = res.json()
    assert fare_res["estimated_fare"] > 0
    print(f"[OK] Fare Calculator API: Estimated fare is INR {fare_res['estimated_fare']}")

    # 8. User Login
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": "john_doe",
        "password": "password123"
    })
    assert res.status_code == 200
    user_token = res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("[OK] User Login Authentication Passed")

    # 9. User Dashboard
    res = requests.get(f"{BASE_URL}/api/dashboard/user", headers=user_headers)
    assert res.status_code == 200
    ud = res.json()
    print(f"[OK] User Dashboard API: User '{ud['user_name']}' loaded successfully")

    # 10. Admin Login
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[OK] Admin Login Authentication Passed")

    # 11. Admin Dashboard Stats
    res = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    ad = res.json()
    assert ad["total_users"] > 0
    print(f"[OK] Admin Analytics Dashboard: {ad['total_users']} users, {ad['total_routes']} routes, {ad['total_stops']} stops")

    # 12. Operator Login & Status Update
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": "operator",
        "password": "operator123"
    })
    assert res.status_code == 200
    op_token = res.json()["access_token"]
    op_headers = {"Authorization": f"Bearer {op_token}"}
    
    res = requests.post(f"{BASE_URL}/api/operator/update-status", headers=op_headers, json={
        "route_id": 1,
        "status": "ON TIME",
        "alert_title": "Normal Schedule Resumed",
        "alert_description": "Route 21A roadworks completed. Normal frequency restored.",
        "priority": "LOW"
    })
    assert res.status_code == 200
    print("[OK] Operator Status Broadcast API Passed")

    # 13. Static Frontend Serving
    res = requests.get(f"{BASE_URL}/index.html")
    assert res.status_code == 200
    assert "<title>Public Transport Information Platform" in res.text
    print("[OK] Frontend Static Mounting Passed")

    print("\nALL 13 END-TO-END TEST SUITES PASSED FLAWLESSLY!")

if __name__ == "__main__":
    test_api()
