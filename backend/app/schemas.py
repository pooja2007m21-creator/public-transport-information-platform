from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- Auth & User Schemas ---
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    phone: Optional[str]
    role: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None

# --- Stop Schemas ---
class StopBase(BaseModel):
    stop_code: str
    stop_name: str
    address: Optional[str] = None
    area: Optional[str] = None
    latitude: float
    longitude: float
    status: Optional[str] = "ACTIVE"

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    stop_code: Optional[str] = None
    stop_name: Optional[str] = None
    address: Optional[str] = None
    area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None

class StopResponse(StopBase):
    id: int

    class Config:
        from_attributes = True

class StopDetailResponse(StopResponse):
    passing_routes: List[dict] = []
    upcoming_buses: List[dict] = []

# --- Route Stop Schemas ---
class RouteStopItem(BaseModel):
    stop_id: int
    stop_order: int

class RouteStopDetail(BaseModel):
    stop_order: int
    stop: StopResponse

    class Config:
        from_attributes = True

# --- Route Schemas ---
class RouteBase(BaseModel):
    route_number: str
    route_name: str
    start_point: str
    destination: str
    description: Optional[str] = None
    distance: float = 0.0
    estimated_duration: int = 30
    fare: float = 20.0
    operating_days: str = "Monday - Sunday"
    status: str = "ACTIVE"
    bus_type: str = "Standard Express"

class RouteCreate(RouteBase):
    stop_ids: Optional[List[int]] = []

class RouteUpdate(BaseModel):
    route_number: Optional[str] = None
    route_name: Optional[str] = None
    start_point: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None
    distance: Optional[float] = None
    estimated_duration: Optional[int] = None
    fare: Optional[float] = None
    operating_days: Optional[str] = None
    status: Optional[str] = None
    bus_type: Optional[str] = None
    stop_ids: Optional[List[int]] = None

class RouteResponse(RouteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    stops_count: Optional[int] = 0

    class Config:
        from_attributes = True

class RouteDetailResponse(RouteResponse):
    stops: List[StopResponse] = []
    schedules: List[dict] = []
    fares: List[dict] = []
    alerts: List[dict] = []

# --- Schedule Schemas ---
class ScheduleBase(BaseModel):
    route_id: int
    stop_id: Optional[int] = None
    departure_time: str
    arrival_time: str
    frequency: str = "15 minutes"
    operating_days: str = "Monday - Sunday"
    status: str = "ON TIME"

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    route_id: Optional[int] = None
    stop_id: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    frequency: Optional[str] = None
    operating_days: Optional[str] = None
    status: Optional[str] = None

class ScheduleResponse(ScheduleBase):
    id: int
    route_number: Optional[str] = None
    route_name: Optional[str] = None
    stop_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Fare Schemas ---
class FareBase(BaseModel):
    route_id: int
    base_fare: float
    student_fare: float
    senior_fare: float
    effective_date: str = "2026-01-01"
    status: str = "ACTIVE"

class FareCreate(FareBase):
    pass

class FareUpdate(BaseModel):
    route_id: Optional[int] = None
    base_fare: Optional[float] = None
    student_fare: Optional[float] = None
    senior_fare: Optional[float] = None
    effective_date: Optional[str] = None
    status: Optional[str] = None

class FareResponse(FareBase):
    id: int
    route_number: Optional[str] = None
    route_name: Optional[str] = None
    distance: Optional[float] = None

    class Config:
        from_attributes = True

class FareCalculateRequest(BaseModel):
    from_stop_id: int
    to_stop_id: int
    passenger_type: Optional[str] = "REGULAR"  # REGULAR, STUDENT, SENIOR

class FareCalculateResponse(BaseModel):
    route_id: int
    route_number: str
    route_name: str
    from_stop: str
    to_stop: str
    stops_count: int
    distance_km: float
    passenger_type: str
    estimated_fare: float
    pass_info: str

# --- Alert Schemas ---
class AlertBase(BaseModel):
    title: str
    description: str
    route_id: Optional[int] = None
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "ACTIVE"  # ACTIVE, RESOLVED, EXPIRED

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    route_id: Optional[int] = None
    priority: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    route_number: Optional[str] = None
    route_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Favorite Schemas ---
class FavoriteCreate(BaseModel):
    route_id: Optional[int] = None
    stop_id: Optional[int] = None
    favorite_type: str = "ROUTE"  # ROUTE, STOP

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    route_id: Optional[int]
    stop_id: Optional[int]
    favorite_type: str
    created_at: datetime
    route: Optional[RouteResponse] = None
    stop: Optional[StopResponse] = None

    class Config:
        from_attributes = True

# --- Search History & Journey Planner Schemas ---
class SearchRequest(BaseModel):
    from_stop: str
    to_stop: str
    travel_date: Optional[str] = None
    travel_time: Optional[str] = None

class JourneyMatchResponse(BaseModel):
    route_id: int
    route_number: str
    route_name: str
    bus_type: str
    from_stop: str
    to_stop: str
    departure_time: str
    arrival_time: str
    duration_min: int
    fare: float
    stops_count: int
    status: str
    operating_days: str

class SearchHistoryResponse(BaseModel):
    id: int
    from_stop: str
    to_stop: str
    search_date: Optional[str]
    search_time: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Dashboard & Stats Schemas ---
class UserDashboardStats(BaseModel):
    user_name: str
    total_favorites: int
    total_saved_stops: int
    recent_searches_count: int
    active_alerts_count: int
    recent_searches: List[SearchHistoryResponse] = []
    favorite_routes: List[dict] = []
    saved_stops: List[dict] = []
    active_alerts: List[AlertResponse] = []

class AdminDashboardStats(BaseModel):
    total_users: int
    total_routes: int
    total_stops: int
    active_routes: int
    active_alerts: int
    total_operators: int
    total_schedules: int
    route_status_breakdown: dict
    alert_priority_breakdown: dict
    recent_users: List[UserResponse] = []
    recent_alerts: List[AlertResponse] = []

class OperatorStatusUpdate(BaseModel):
    route_id: int
    status: str  # ON TIME, DELAYED, SUSPENDED, CANCELLED, MAINTENANCE
    alert_title: Optional[str] = None
    alert_description: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
