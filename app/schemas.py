from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class IngestPayload(SQLModel):
    tag_id: str = Field(..., min_length=1)
    event: str = Field(..., min_length=1)
    rssi: int
    channel: int
    source: str = Field(..., min_length=1)
    timestamp: datetime


class TagPublic(SQLModel):
    tag_id: str
    last_seen: datetime
    rssi: int
    status: str
    last_event: str
    channel: int
    source: str


class EventPublic(SQLModel):
    id: Optional[int] = None
    time: datetime
    tag_id: str
    type: str
    rssi: int
    source: str
    channel: int


class StatusPublic(SQLModel):
    esp32_connected: bool
    wrap260_connected: bool
    channel: Optional[int]
    last_update: Optional[datetime]
    tags_detected: int

class EspConfigBase(SQLModel):
    tx_power: int
    n: PathLossExponent = PathLossExponent.FREE_SPACE

class EspConfigCreate(EspConfigBase):
    pass

class EspConfigPublic(EspConfigBase):
    id: int

class EspConfigUpdate(SQLModel):
    tx_power: Optional[int] = None
    n: Optional[PathLossExponent] = None
