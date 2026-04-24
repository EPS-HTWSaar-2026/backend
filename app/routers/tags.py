from fastapi import APIRouter

from ..db import SessionDep
from ..schemas import TagPublic
from ..services import get_tags_with_fresh_status

router = APIRouter(prefix="/api", tags=["tags"])


@router.get("/tags", response_model=list[TagPublic])
def tags(session: SessionDep):
    return get_tags_with_fresh_status(session)