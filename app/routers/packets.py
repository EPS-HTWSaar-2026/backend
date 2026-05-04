from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..database import SessionDep
from ..schemas import PacketResponse
from ..services import get_packets, get_packet, delete_packet

router = APIRouter(prefix="/api/packets", tags=["packets"])


@router.get("", response_model=list[PacketResponse])
def list_packets(
    session: SessionDep,
    tag_mac: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    return get_packets(session, tag_mac=tag_mac, limit=limit)


@router.get("/{packet_id}", response_model=PacketResponse)
def read_packet(packet_id: int, session: SessionDep):
    packet = get_packet(packet_id, session)
    if packet is None:
        raise HTTPException(status_code=404, detail="Packet not found")
    return packet


@router.delete("/{packet_id}", status_code=204)
def remove_packet(packet_id: int, session: SessionDep):
    if not delete_packet(packet_id, session):
        raise HTTPException(status_code=404, detail="Packet not found")