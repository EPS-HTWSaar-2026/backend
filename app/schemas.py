from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class IngestPayload(SQLModel):
    tag_id: str = Field(..., min_length=1)
    rssi: int
    source: str = Field(..., min_length=1)
    timestamp: datetime