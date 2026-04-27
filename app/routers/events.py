from fastapi import APIRouter, Query

from ..database import SessionDep
from ..schemas import EventPublic
from ..services import get_recent_events

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events", response_model=list[EventPublic])
def events(session: SessionDep, limit: int = Query(default=50, ge=1, le=500)):
    return get_recent_events(session, limit=limit)