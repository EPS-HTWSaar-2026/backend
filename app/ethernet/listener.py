import asyncio
import logging
from datetime import datetime, timezone

from sqlmodel import Session

from ..config import settings
from ..database import engine
from ..schemas import IngestPayload
from ..services import ingest_payload
from .parser import parse_packet

logger = logging.getLogger(__name__)

CHANNEL_PORTS: dict[int, int] = {
    1: settings.esp_port_1,
    2: settings.esp_port_2,
    3: settings.esp_port_3,
}


def _save_packet_sync(payload: IngestPayload) -> None:
    try:
        with Session(engine) as session:
            ingest_payload(payload, session)
    except Exception as e:
        logger.exception("Database error while saving tag %s: %s", payload.tag_id, e)


async def _save_packet_async(mac_tag: str, mac_esp: str, rssi: int) -> None:
    payload = IngestPayload(
        tag_id=mac_tag,
        rssi=rssi,
        source=mac_esp,
        timestamp=datetime.now(timezone.utc),
    )
    await asyncio.to_thread(_save_packet_sync, payload)


async def _listen_channel(channel: int, host: str, port: int) -> None:
    logger.info("Channel %d: starting listener %s:%d", channel, host, port)
    while True:
        try:
            logger.info("Channel %d: connecting to %s:%d", channel, host, port)
            reader, writer = await asyncio.open_connection(host, port)
            logger.info("Channel %d: connected.", channel)

            try:
                while True:
                    line = await reader.readline()
                    if not line:
                        logger.warning("Channel %d: connection closed by remote.", channel)
                        break

                    parsed = parse_packet(line)
                    if parsed is None:
                        logger.debug("Channel %d: failed to parse line: %r", channel, line)
                        continue

                    try:
                        await _save_packet_async(
                            mac_tag=parsed.mac_tag,
                            mac_esp=parsed.mac_esp,
                            rssi=parsed.rssi,
                        )
                        logger.debug(
                            "Channel %d: saved tag=%s rssi=%d",
                            channel, parsed.mac_tag, parsed.rssi
                        )
                    except Exception:
                        logger.exception("Channel %d: error saving tag %s", channel, parsed.mac_tag)

            finally:
                writer.close()
                await writer.wait_closed()

        except (ConnectionRefusedError, OSError) as exc:
            logger.error(
                "Channel %d: network error %s. Retrying in %.0fs",
                channel, exc, settings.reconnect_delay
            )
        except Exception:
            logger.exception("Channel %d: unexpected error. Retrying", channel)

        await asyncio.sleep(settings.reconnect_delay)


async def start_ethernet_listeners() -> list[asyncio.Task]:
    tasks: list[asyncio.Task] = []
    for channel, port in CHANNEL_PORTS.items():
        task = asyncio.create_task(
            _listen_channel(channel, settings.esp_host, port),
            name=f"ethernet-listener-ch{channel}",
        )
        tasks.append(task)
        logger.info("Channel %d: background task created (port %d).", channel, port)
    return tasks