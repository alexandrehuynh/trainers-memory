"""
SQLAlchemy models for database tables.

This module defines the database schema using SQLAlchemy ORM models.
These models map directly to tables in the database.
"""

import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, DateTime, func, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .config import Base, metadata
from .models_helper import get_table_args, get_foreign_key_target

class Client(Base):
    """Client model representing fitness clients/users."""
    __tablename__ = "clients"
    __table_args__ = get_table_args([
        Index('ix_clients_email', 'email'),
        Index('ix_clients_name', 'name')
    ])
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    api_key = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    workouts = relationship("Workout", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client {self.name}>"

class Workout(Base):
    """Workout model representing a client's workout session."""
    __tablename__ = "workouts"
    __table_args__ = get_table_args([
        Index('ix_workouts_client_id', 'client_id'),
        Index('ix_workouts_date', 'date')
    ])
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey(get_foreign_key_target("clients.id"), ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    workout_type = Column(String(255), nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in minutes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="workouts")
    exercises = relationship("Exercise", back_populates="workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workout {self.id} - {self.date}>"

class Exercise(Base):
    """Exercise model representing an exercise within a workout."""
    __tablename__ = "exercises"
    __table_args__ = get_table_args([
        Index('ix_exercises_workout_id', 'workout_id')
    ])
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey(get_foreign_key_target("workouts.id"), ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)  # Weight in user's preferred unit
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    workout = relationship("Workout", back_populates="exercises")
    
    def __repr__(self):
        return f"<Exercise {self.name}>"

class APIKey(Base):
    """API Key model for tracking API keys and their owners."""
    __tablename__ = "api_keys"
    __table_args__ = get_table_args([
        Index('ix_api_keys_key', 'key'),
        Index('ix_api_keys_client_id', 'client_id')
    ])
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False, unique=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey(get_foreign_key_target("clients.id"), ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<APIKey {self.name}>" 