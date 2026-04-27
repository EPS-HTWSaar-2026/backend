from fastapi import APIRouter

from ..database import SessionDep
from ..schemas import StatusPublic
from ..services import get_status

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=StatusPublic)
def status(session: SessionDep):
    return get_status(session)