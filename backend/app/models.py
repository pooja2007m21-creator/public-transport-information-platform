from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="USER", nullable=False)  # USER, OPERATOR, ADMIN
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, SUSPENDED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_number = Column(String(20), unique=True, index=True, nullable=False)
    route_name = Column(String(100), nullable=False)
    start_point = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    distance = Column(Float, default=0.0)  # in km
    estimated_duration = Column(Integer, default=30)  # in minutes
    fare = Column(Float, default=20.0)  # standard base fare
    operating_days = Column(String(100), default="Monday - Sunday")
    status = Column(String(20), default="ACTIVE")  # ACTIVE, DELAYED, SUSPENDED, CANCELLED, MAINTENANCE
    bus_type = Column(String(50), default="Standard Express")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    route_stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.stop_order")
    schedules = relationship("Schedule", back_populates="route", cascade="all, delete-orphan")
    fares = relationship("Fare", back_populates="route", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="route", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="route", cascade="all, delete-orphan")

class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    stop_code = Column(String(20), unique=True, index=True, nullable=False)
    stop_name = Column(String(100), index=True, nullable=False)
    address = Column(String(255), nullable=True)
    area = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE

    # Relationships
    route_stops = relationship("RouteStop", back_populates="stop", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="stop", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="stop", cascade="all, delete-orphan")

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)
    stop_order = Column(Integer, nullable=False)

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=True)
    departure_time = Column(String(20), nullable=False)
    arrival_time = Column(String(20), nullable=False)
    frequency = Column(String(50), default="15 minutes")
    operating_days = Column(String(100), default="Monday - Sunday")
    status = Column(String(20), default="ON TIME")  # ON TIME, DELAYED, CANCELLED, SUSPENDED

    route = relationship("Route", back_populates="schedules")
    stop = relationship("Stop", back_populates="schedules")

class Fare(Base):
    __tablename__ = "fares"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    base_fare = Column(Float, nullable=False)
    student_fare = Column(Float, nullable=False)
    senior_fare = Column(Float, nullable=False)
    effective_date = Column(String(20), default="2026-01-01")
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE

    route = relationship("Route", back_populates="fares")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, RESOLVED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="alerts")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=True)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=True)
    favorite_type = Column(String(20), default="ROUTE")  # ROUTE, STOP
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    route = relationship("Route", back_populates="favorites")
    stop = relationship("Stop", back_populates="favorites")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    from_stop = Column(String(100), nullable=False)
    to_stop = Column(String(100), nullable=False)
    search_date = Column(String(20), nullable=True)
    search_time = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="search_history")
