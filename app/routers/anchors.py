from fastapi import APIRouter, HTTPException

from ..database import SessionDep
from ..models import Anchor
from ..schemas import AnchorCreate, AnchorPublic, AnchorUpdate
from ..services import get_anchors, upsert_anchor, delete_anchor

router = APIRouter(prefix="/api", tags=["anchors"])


@router.get("/anchors", response_model=list[AnchorPublic])
def list_anchors(session: SessionDep):
    return get_anchors(session)


@router.post("/anchors", response_model=AnchorPublic)
def create_anchor(anchor: AnchorCreate, session: SessionDep):
    return upsert_anchor(anchor, session)


@router.put("/anchors/{esp_mac}", response_model=AnchorPublic)
def update_anchor(esp_mac: str, anchor: AnchorUpdate, session: SessionDep):
    existing = session.get(Anchor, esp_mac)
    if not existing:
        raise HTTPException(status_code=404, detail="Anchor not found")
    return upsert_anchor(AnchorCreate(esp_mac=esp_mac, **anchor.model_dump()), session)


@router.delete("/anchors/{esp_mac}")
def remove_anchor(esp_mac: str, session: SessionDep):
    existing = session.get(Anchor, esp_mac)
    if not existing:
        raise HTTPException(status_code=404, detail="Anchor not found")
    delete_anchor(esp_mac, session)
    return {"ok": True}
