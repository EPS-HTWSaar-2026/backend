from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    tag_id: str = Field(primary_key=True, index=True)
    last_seen: datetime
    rssi: int
    status: str
    last_event: str
    channel: int
    source: str


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime = Field(index=True)
    tag_id: str = Field(index=True)
    type: str = Field(index=True)
    rssi: int
    source: str
    channel: int


class SystemState(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    wrap260_connected: bool = Field(default=True)