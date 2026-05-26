import logging
from datetime import datetime, timezone

import numpy as np
from sqlmodel import Session, select

from ..database import engine
from ..models import Tag, Listener, Packet
from ..websocket import publish
from .parser import ParsedPacket, _format_mac

logger = logging.getLogger(__name__)


def rssi_to_distance(rssi: int, rssi_ref: int, n: float = 2.0) -> float:
    return 10 ** ((rssi_ref - rssi) / (10 * n))


def trilaterate(p1, p2, p3, r1, r2, r3):
    temp1 = p2 - p1
    e_x = temp1 / np.linalg.norm(temp1)
    temp2 = p3 - p1
    i = np.dot(e_x, temp2)
    temp3 = temp2 - i * e_x
    e_y = temp3 / np.linalg.norm(temp3)
    d = np.linalg.norm(p2 - p1)
    j = np.dot(e_y, temp2)
    x = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    y = (r1 * r1 - r3 * r3 - 2 * i * x + i * i + j * j) / (2 * j)
    temp4 = r1 * r1 - x * x - y * y
    z = 0.0 if temp4 < 0 else float(np.sqrt(temp4))
    return p1 + x * e_x + y * e_y + z * np.cross(e_x, e_y)


def compute_error(point, p1, p2, p3, r1, r2, r3):
    residuals = np.array([
        np.linalg.norm(point - p1) - r1,
        np.linalg.norm(point - p2) - r2,
        np.linalg.norm(point - p3) - r3,
    ])
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    confidence_radius = float(np.max(np.abs(residuals)))
    return residuals, rmse, confidence_radius



# def _save_packets(packets: list[ParsedPacket], session: Session) -> None:
#     now = datetime.now(timezone.utc)
#     for p in packets:
#         if session.get(Tag, p.mac_tag) is None:
#             session.add(Tag(tag_mac=p.mac_tag))
#             try:
#                 session.flush()
#             except Exception:
#                 session.rollback()
#
#         session.add(Packet(
#             tag_mac=p.mac_tag,
#             esp_mac=p.mac_esp,
#             rssi=p.rssi,
#             timestamp=now,
#         ))

async def on_group_ready(packets: list[ParsedPacket]) -> None:
    try:
        with Session(engine) as session:
            listeners = {
                _format_mac(l.esp_mac): l
                for l in session.exec(select(Listener)).all()
                if l.x is not None and l.y is not None
            }

            usable = [p for p in packets if p.mac_esp in listeners]

            # _save_packets(usable, session)  <-- DELETED THIS LINE

            if len(usable) < 3:
                logger.debug(
                    "Group for tag %s has only %d usable listener(s) — skipping trilateration",
                    packets[0].mac_tag, len(usable)
                )
                session.commit()
                return
