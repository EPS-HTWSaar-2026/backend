from fastapi import APIRouter, HTTPException

from ..database import SessionDep
from ..schemas import ListenerCreate, ListenerResponse, ListenerUpdate
from ..services import (
    create_listener,
    delete_listener,
    get_listener,
    get_listeners,
    update_listener,
)

router = APIRouter(prefix="/api/listeners", tags=["listeners"])


@router.get("", response_model=list[ListenerResponse])
def list_listeners(session: SessionDep):
    return get_listeners(session)


@router.get("/{esp_mac}", response_model=ListenerResponse)
def read_listener(esp_mac: str, session: SessionDep):
    listener = get_listener(esp_mac, session)
    if listener is None:
        raise HTTPException(status_code=404, detail="Listener not found")
    return listener


@router.post("", response_model=ListenerResponse, status_code=201)
def add_listener(body: ListenerCreate, session: SessionDep):
    return create_listener(body.esp_mac, body.rssi_ref, body.x, body.y, session)


@router.patch("/{esp_mac}", response_model=ListenerResponse)
def patch_listener(esp_mac: str, body: ListenerUpdate, session: SessionDep):
    """Partial update of listener calibration data or position."""
    listener = update_listener(esp_mac, body.rssi_ref, body.x, body.y, session)
    if listener is None:
        raise HTTPException(status_code=404, detail="Listener not found")
    return listener


@router.delete("/{esp_mac}", status_code=204)
def remove_listener(esp_mac: str, session: SessionDep):
    if not delete_listener(esp_mac, session):
        raise HTTPException(status_code=404, detail="Listener not found")
