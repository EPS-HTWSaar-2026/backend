from datetime import datetime
from typing import Optional
from enum import IntEnum

from sqlmodel import Field, SQLModel


class PathLossExponent(IntEnum):
    ERROR = 1
    FREE_SPACE = 2
    ROOM = 3
    WALL = 4


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


class EspConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tx_power: int
    n: PathLossExponent = Field(default=PathLossExponent.FREE_SPACE)
