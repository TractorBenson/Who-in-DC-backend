from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    ENTER = "enter"
    LEAVE = "leave"


class PresenceEvent(BaseModel):
    id: str
    user_id: str
    type: EventType
    at: str
    name_snapshot: str


class PresenceStore(BaseModel):
    schema_version: int = 1
    created_at: str
    updated_at: str
    users: dict[str, str] = Field(default_factory=dict)
    events: list[PresenceEvent] = Field(default_factory=list)
    active: dict[str, str] = Field(default_factory=dict)
