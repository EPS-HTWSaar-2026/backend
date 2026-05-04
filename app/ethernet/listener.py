import asyncio
import logging
from datetime import datetime, timezone

from sqlmodel import Session

from ..config import settings
from ..database import engine
from ..services import save_packet
from .parser import parse_packet

logger = logging.getLogger(__name__)

CHANNEL_PORTS: dict[int, int] = {
    1: settings.esp_port_1,
    2: settings.esp_port_2,
    3: settings.esp_port_3,
}


def _save_packet_sync(tag_mac: str, esp_mac: str, rssi: int) -> None:
    with Session(engine) as session:
        save_packet(
            tag_mac=tag_mac,
            esp_mac=esp_mac,
            rssi=rssi,
            timestamp=datetime.now(timezone.utc),
            session=session,
        )


async def _listen_channel(channel: int, host: str, port: int) -> None:
    logger.info("Channel %d: starting listener %s:%d", channel, host, port)

    while True:
        writer = None
        try:
            logger.info("Channel %d: connecting to %s:%d", channel, host, port)
            reader, writer = await asyncio.open_connection(host, port)
            logger.info("Channel %d: connected.", channel)

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
                    await asyncio.to_thread(
                        _save_packet_sync, parsed.mac_tag, parsed.mac_esp, parsed.rssi
                    )
                    logger.debug("Channel %d: saved tag=%s rssi=%d", channel, parsed.mac_tag, parsed.rssi)
                except Exception:
                    logger.exception("Channel %d: error saving tag %s", channel, parsed.mac_tag)

        except (ConnectionRefusedError, OSError) as exc:
            logger.error("Channel %d: network error %s. Retrying in %.0fs", channel, exc, settings.reconnect_delay)
        except Exception:
            logger.exception("Channel %d: unexpected error. Retrying", channel)
        finally:
            if writer is not None:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

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