from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ClientBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: UUID
    trainer_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkoutRecordBase(BaseModel):
    client_id: UUID
    date: datetime = Field(default_factory=datetime.now)
    exercise: str
    sets: int
    reps: int
    weight: float
    notes: Optional[str] = None
    modifiers: Optional[str] = None

class WorkoutRecordCreate(WorkoutRecordBase):
    pass

class WorkoutRecord(WorkoutRecordBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class VoiceNote(BaseModel):
    id: UUID
    client_id: UUID
    trainer_id: UUID
    date: datetime
    audio_url: str
    transcript: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIAnalysisRequest(BaseModel):
    client_id: UUID
    query: str
    
class AIAnalysisResponse(BaseModel):
    answer: str
    data: Optional[dict] = None 