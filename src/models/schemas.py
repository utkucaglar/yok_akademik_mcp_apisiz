from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class Specialty(BaseModel):
    id: int
    name: str

class Field(BaseModel):
    id: int
    name: str
    specialties: List[Specialty]

class AcademicProfile(BaseModel):
    id: int
    name: str
    title: str
    url: str
    info: str
    photoUrl: str
    header: str
    green_label: str
    blue_label: str
    keywords: str
    email: str

class Collaborator(BaseModel):
    id: int
    name: str
    title: str
    info: str
    green_label: str
    blue_label: str
    keywords: str
    photoUrl: str
    status: str
    deleted: bool
    url: str
    email: str

class SearchRequest(BaseModel):
    name: str
    field_id: Optional[int] = None
    specialty_ids: Optional[str] = None
    email: Optional[str] = None
    max_results: int = 100

class CollaboratorRequest(BaseModel):
    session_id: str
    profile_id: Optional[int] = None
    profile_url: Optional[str] = None

class SessionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SessionInfo(BaseModel):
    session_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    profiles_count: Optional[int] = None
    collaborators_count: Optional[int] = None
    error_message: Optional[str] = None

class SearchResponse(BaseModel):
    session_id: str
    profiles: List[AcademicProfile]
    total_count: int
    status: SessionStatus

class CollaboratorResponse(BaseModel):
    session_id: str
    collaborators: List[Collaborator]
    total_count: int
    status: SessionStatus 