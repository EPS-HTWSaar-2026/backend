import asyncio
import logging
import numpy as np
from sqlmodel import Session, select
from ..database import engine
from ..models import Tag, Listener, Packet
from ..websocket import publish

logger = logging.getLogger(__name__)

queue = []

def rssi_to_distance(rssi: int, rssi_ref: int, n: float = 2.0) -> float:
    return 10 ** ((rssi_ref - rssi) / (10 * n))

def trilaterate(p1, p2, p3, r1, r2, r3):
    temp1 = p2 - p1
    e_x = temp1 / np.linalg.norm(temp1)
    temp2 = p3 - p1
    i = np.dot(e_x, temp2)
    temp3 = temp2 - i * e_x
    e_y = temp3 / np.linalg.norm(temp3)
    e_z = np.cross(e_x, e_y)

    d = np.linalg.norm(p2 - p1)
    j = np.dot(e_y, temp2)

    x = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    y = (r1 * r1 - r3 * r3 - 2 * i * x + i * i + j * j) / (2 * j)

    temp4 = r1 * r1 - x * x - y * y
    if temp4 < 0:
        z = 0.0
    else:
        z = np.sqrt(temp4)

    return p1 + x * e_x + y * e_y + z * e_z


def compute_error(point, p1, p2, p3, r1, r2, r3):
    d1 = np.norm(point - p1)
    d2 = np.norm(point - p2)
    d3 = np.norm(point - p3)

    residuals = np.array([
        d1 - r1,
        d2 - r2,
        d3 - r3
    ])

    rmse = np.sqrt(np.mean(residuals ** 2))
    confidence_radius = np.max(np.abs(residuals))

    return residuals, rmse, confidence_radius



async def location_engine_task():
    logger.info("Starting RTLS Location Engine...")

    while True:
        await asyncio.sleep(1.0)  # Run calculation cycle every second

        try:
            with Session(engine) as session:
                # Fetch all listeners that have configured coordinates
                listeners = session.exec(select(Listener)).all()
                valid_listeners = {
                    l.esp_mac: l for l in listeners
                    if l.x is not None and l.y is not None
                }

                if len(valid_listeners) < 3:
                    logger.info("No listeners found")
                    continue  # We need at least 3 configured anchors to trilaterate

                tags = session.exec(select(Tag)).all()

                for tag in tags:
                    latest_packets = []

                    # Get the most recent packet from each known listener for this tag
                    for esp_mac in valid_listeners.keys():
                        stmt = select(Packet).where(
                            Packet.tag_mac == tag.tag_mac,
                            Packet.esp_mac == esp_mac
                        ).order_by(Packet.timestamp.desc()).limit(1)

                        packet = session.exec(stmt).first()
                        if packet:
                            latest_packets.append(packet)

                    # If we have packets from at least 3 distinct ESPs, calculate
                    if len(latest_packets) >= 3:
                        # Grab the 3 most recent
                        latest_packets.sort(key=lambda p: p.timestamp, reverse=True)
                        pks = latest_packets[:3]

                        l1, l2, l3 = [valid_listeners[p.esp_mac] for p in pks]

                        p1 = np.array([l1.x, l1.y, 0.0])
                        p2 = np.array([l2.x, l2.y, 0.0])
                        p3 = np.array([l3.x, l3.y, 0.0])

                        r1 = rssi_to_distance(pks[0].rssi, l1.rssi_ref)
                        r2 = rssi_to_distance(pks[1].rssi, l2.rssi_ref)
                        r3 = rssi_to_distance(pks[2].rssi, l3.rssi_ref)

                        try:
                            point = trilaterate(p1, p2, p3, r1, r2, r3)
                            residuals, rmse, confidence = compute_error(point, p1, p2, p3, r1, r2, r3)

                            # 1. Update tag position in Database
                            tag.x = float(point[0])
                            tag.y = float(point[1])
                            session.add(tag)

                            # 2. Publish updated location via WebSockets
                            await publish({
                                "tag_mac": tag.tag_mac,
                                "x": tag.x,
                                "y": tag.y,
                                "errors": {residuals, rmse, confidence},
                            })

                        except Exception as e:
                            logger.error(f"Trilateration failed for tag {tag.tag_mac}: {e}")

                session.commit()

        except Exception as e:
            logger.error(f"Error in location engine: {e}")