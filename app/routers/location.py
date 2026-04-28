from fastapi import APIRouter, Query
from typing import Optional

from ..database import SessionDep
from ..schemas import RawPacketPublic, TrilaterationResultPublic
from ..services import get_raw_packets, get_trilateration_results

router = APIRouter(prefix="/api", tags=["location"])


@router.get("/packets", response_model=list[RawPacketPublic])
def raw_packets(
    session: SessionDep,
    tag_mac: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    return get_raw_packets(session, tag_mac=tag_mac, limit=limit)


@router.get("/positions", response_model=list[TrilaterationResultPublic])
def positions(
    session: SessionDep,
    tag_mac: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    return get_trilateration_results(session, tag_mac=tag_mac, limit=limit)
