from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .models import Tag, Listener, Packet
from .schemas import TagResponse, ListenerResponse, PacketResponse


# --- Tags ---

def get_tags(session: Session) -> list[TagResponse]:
    tags = session.exec(select(Tag)).all()
    return [TagResponse(tag_mac=t.tag_mac, x=t.x, y=t.y) for t in tags]


def get_tag(tag_mac: str, session: Session) -> Optional[TagResponse]:
    tag = session.get(Tag, tag_mac)
    if tag is None:
        return None
    return TagResponse(tag_mac=tag.tag_mac, x=tag.x, y=tag.y)


def update_tag(tag_mac: str, x: Optional[float], y: Optional[float], session: Session) -> Optional[TagResponse]:
    tag = session.get(Tag, tag_mac)
    if tag is None:
        return None
    
    if x is not None:
        tag.x = x
    if y is not None:
        tag.y = y
        
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return TagResponse(tag_mac=tag.tag_mac, x=tag.x, y=tag.y)


def delete_tag(tag_mac: str, session: Session) -> bool:
    tag = session.get(Tag, tag_mac)
    if tag is None:
        return False
    session.delete(tag)
    session.commit()
    return True


# --- Listeners ---
def get_listeners(session: Session) -> list[ListenerResponse]:
    listeners = session.exec(select(Listener)).all()
    return [ListenerResponse(esp_mac=l.esp_mac, rssi_ref=l.rssi_ref, x=l.x, y=l.y) for l in listeners]


def get_listener(esp_mac: str, session: Session) -> Optional[ListenerResponse]:
    listener = session.get(Listener, esp_mac)
    if listener is None:
        return None
    return ListenerResponse(esp_mac=listener.esp_mac, rssi_ref=listener.rssi_ref, x=listener.x, y=listener.y)


def create_listener(esp_mac: str, rssi_ref: int, x: Optional[float], y: Optional[float],
                    session: Session) -> ListenerResponse:
    listener = session.get(Listener, esp_mac)
    if listener is None:
        listener = Listener(esp_mac=esp_mac, rssi_ref=rssi_ref, x=x, y=y)
    else:
        listener.rssi_ref = rssi_ref
        if x is not None:
            listener.x = x
        if y is not None:
            listener.y = y
            
    session.add(listener)
    session.commit()
    session.refresh(listener)
    return ListenerResponse(esp_mac=listener.esp_mac, rssi_ref=listener.rssi_ref, x=listener.x, y=listener.y)


def update_listener(esp_mac: str, rssi_ref: Optional[int], x: Optional[float], y: Optional[float], session: Session) -> Optional[ListenerResponse]:
    listener = session.get(Listener, esp_mac)
    if listener is None:
        return None

    if rssi_ref is not None:
        listener.rssi_ref = rssi_ref
    if x is not None:
        listener.x = x
    if y is not None:
        listener.y = y

    session.add(listener)
    session.commit()
    session.refresh(listener)
    return ListenerResponse(esp_mac=listener.esp_mac, rssi_ref=listener.rssi_ref, x=listener.x, y=listener.y)


def delete_listener(esp_mac: str, session: Session) -> bool:
    listener = session.get(Listener, esp_mac)
    if listener is None:
        return False
    session.delete(listener)
    session.commit()
    return True


# --- Packets ---

def save_packet(tag_mac: str, esp_mac: str, rssi: int, raw_packet: str, rx_ctrl: dict, timestamp: datetime, session: Session) -> None:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    # Auto-create tag if first time seen
    if session.get(Tag, tag_mac) is None:
        session.add(Tag(tag_mac=tag_mac))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()

    session.add(Packet(
        tag_mac=tag_mac, 
        esp_mac=esp_mac, 
        rssi=rssi, 
        raw_packet=raw_packet, 
        rx_ctrl=rx_ctrl, 
        timestamp=timestamp
    ))
    session.commit()


def get_packets(session: Session, tag_mac: Optional[str] = None, limit: int = 100) -> list[PacketResponse]:
    statement = select(Packet)
    if tag_mac:
        statement = statement.where(Packet.tag_mac == tag_mac)
    statement = statement.order_by(Packet.timestamp.desc()).limit(limit)
    packets = session.exec(statement).all()
    return [
        PacketResponse(
            id=p.id, 
            tag_mac=p.tag_mac, 
            esp_mac=p.esp_mac, 
            rssi=p.rssi, 
            raw_packet=p.raw_packet,
            rx_ctrl=p.rx_ctrl,
            timestamp=p.timestamp
        )
        for p in packets
    ]


def get_packet(packet_id: int, session: Session) -> Optional[PacketResponse]:
    packet = session.get(Packet, packet_id)
    if packet is None:
        return None
    return PacketResponse(
        id=packet.id, 
        tag_mac=packet.tag_mac, 
        esp_mac=packet.esp_mac, 
        rssi=packet.rssi, 
        raw_packet=packet.raw_packet,
        rx_ctrl=packet.rx_ctrl,
        timestamp=packet.timestamp
    )

def delete_packet(packet_id: int, session: Session) -> bool:
    packet = session.get(Packet, packet_id)
    if packet is None:
        return False
    session.delete(packet)
    session.commit()
    return True
