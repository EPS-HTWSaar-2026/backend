from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    tag_mac: str = Field(primary_key=True, index=True)
    x: Optional[float] = None
    y: Optional[float] = None


class Listener(SQLModel, table=True):
    esp_mac: str = Field(primary_key=True, index=True)
    rssi_ref: int
    x: Optional[float] = None
    y: Optional[float] = None


class Packet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tag_mac: str = Field(index=True)
    esp_mac: str = Field(index=True)
    rssi: int
    raw_packet: str
    rx_ctrl: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime = Field(index=True)
