from fastapi import APIRouter, HTTPException

from ..database import SessionDep
from ..schemas import TagResponse, TagUpdate
from ..services import delete_tag, get_tag, get_tags, update_tag

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(session: SessionDep):
    return get_tags(session)


@router.get("/{tag_mac}", response_model=TagResponse)
def read_tag(tag_mac: str, session: SessionDep):
    tag = get_tag(tag_mac, session)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.patch("/{tag_mac}", response_model=TagResponse)
def patch_tag(tag_mac: str, body: TagUpdate, session: SessionDep):
    """Manually override the position of a tag."""
    tag = update_tag(tag_mac, body.x, body.y, session)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_mac}", status_code=204)
def remove_tag(tag_mac: str, session: SessionDep):
    if not delete_tag(tag_mac, session):
        raise HTTPException(status_code=404, detail="Tag not found")
