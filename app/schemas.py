from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


# --- Packet ---

class PacketResponse(SQLModel):
    id: Optional[int] = None
    tag_mac: str
    esp_mac: str
    rssi: int
    timestamp: datetime


# --- Tag ---

class TagResponse(SQLModel):
    tag_mac: str
    x: Optional[float] = None
    y: Optional[float] = None


class TagUpdate(SQLModel):
    x: Optional[float] = None
    y: Optional[float] = None


# --- Listener ---

class ListenerResponse(SQLModel):
    esp_mac: str
    x: Optional[float] = None
    y: Optional[float] = None


class ListenerCreate(SQLModel):
    esp_mac: str
    x: Optional[float] = None
    y: Optional[float] = None


class ListenerUpdate(SQLModel):
    x: Optional[float] = None
    y: Optional[float] = None