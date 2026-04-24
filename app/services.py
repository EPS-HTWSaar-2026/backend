from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from .models import Tag, Event, SystemState
from .schemas import IngestPayload, TagPublic, EventPublic, StatusPublic


ONLINE_THRESHOLD_SECONDS = 10
STALE_THRESHOLD_SECONDS = 30


def normalize_event(event: str) -> str:
    event = event.strip().lower()
    if event in {"heartbeat", "button", "detected"}:
        return event
    return "unknown"


def compute_tag_status(last_seen: datetime, now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    delta = (now - last_seen).total_seconds()

    if delta <= ONLINE_THRESHOLD_SECONDS:
        return "online"
    if delta <= STALE_THRESHOLD_SECONDS:
        return "stale"
    return "offline"


def ingest_payload(payload: IngestPayload, session: Session) -> dict:
    normalized_event = normalize_event(payload.event)

    timestamp = payload.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    db_tag = session.get(Tag, payload.tag_id)

    if db_tag is None:
        db_tag = Tag(
            tag_id=payload.tag_id,
            last_seen=timestamp,
            rssi=payload.rssi,
            status="online",
            last_event=normalized_event,
            channel=payload.channel,
            source=payload.source,
        )
    else:
        db_tag.last_seen = timestamp
        db_tag.rssi = payload.rssi
        db_tag.status = "online"
        db_tag.last_event = normalized_event
        db_tag.channel = payload.channel
        db_tag.source = payload.source

    db_event = Event(
        time=timestamp,
        tag_id=payload.tag_id,
        type=normalized_event,
        rssi=payload.rssi,
        source=payload.source,
        channel=payload.channel,
    )

    session.add(db_tag)
    session.add(db_event)
    session.commit()
    session.refresh(db_tag)
    session.refresh(db_event)

    return {
        "ok": True,
        "message": "Payload processed successfully",
        "tag_id": db_tag.tag_id,
        "event_id": db_event.id,
    }


def get_tags_with_fresh_status(session: Session) -> list[TagPublic]:
    now = datetime.now(timezone.utc)

    statement = select(Tag).order_by(Tag.last_seen.desc())
    tags = session.exec(statement).all()

    refreshed = []
    for tag in tags:
        refreshed.append(
            TagPublic(
                tag_id=tag.tag_id,
                last_seen=tag.last_seen,
                rssi=tag.rssi,
                status=compute_tag_status(tag.last_seen, now),
                last_event=tag.last_event,
                channel=tag.channel,
                source=tag.source,
            )
        )
    return refreshed


def get_recent_events(session: Session, limit: int = 50) -> list[EventPublic]:
    statement = select(Event).order_by(Event.time.desc()).limit(limit)
    events = session.exec(statement).all()

    return [
        EventPublic(
            id=event.id,
            time=event.time,
            tag_id=event.tag_id,
            type=event.type,
            rssi=event.rssi,
            source=event.source,
            channel=event.channel,
        )
        for event in events
    ]


def get_status(session: Session) -> StatusPublic:
    now = datetime.now(timezone.utc)

    last_event_statement = select(Event).order_by(Event.time.desc()).limit(1)
    last_event = session.exec(last_event_statement).first()

    system_state = session.get(SystemState, 1)
    if system_state is None:
        system_state = SystemState(id=1, wrap260_connected=True)
        session.add(system_state)
        session.commit()
        session.refresh(system_state)

    last_update = last_event.time if last_event else None
    last_channel = last_event.channel if last_event else None

    esp32_connected = False
    if last_update is not None:
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        esp32_connected = (now - last_update).total_seconds() <= 15

    count_statement = select(Tag)
    tags_detected = len(session.exec(count_statement).all())

    return StatusPublic(
        esp32_connected=esp32_connected,
        wrap260_connected=system_state.wrap260_connected,
        channel=last_channel,
        last_update=last_update,
        tags_detected=tags_detected,
    )