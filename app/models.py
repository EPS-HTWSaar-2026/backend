from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    tag_id: int = Field(primary_key=True, index=True)
    tag_mac: str
    last_seen: datetime
    rssi: int
    source: str