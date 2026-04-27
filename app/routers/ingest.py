from fastapi import APIRouter

from ..db import SessionDep
from ..schemas import IngestPayload
from ..services import ingest_payload

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest")
def ingest(data: IngestPayload, session: SessionDep):
    return ingest_payload(data, session)