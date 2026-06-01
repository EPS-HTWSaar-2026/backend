import asyncio
import logging
import time
from datetime import datetime, timezone

from sqlmodel import Session

from ..config import settings
from ..database import engine
from ..services import save_packet
from ..websocket import publish_packet
from .grouper import BeaconGrouper
from .parser import ParsedPacket, parse_packet

logger = logging.getLogger(__name__)

CHANNEL_PORTS: dict[int, int] = {
    1: settings.esp_port_1,
    2: settings.esp_port_2,
    3: settings.esp_port_3,
}


def _store_packet_sync(parsed: ParsedPacket) -> None:
    """Persist the packet; runs in a thread pool so it never blocks the event loop."""
    try:
        with Session(engine) as session:
            save_packet(
                tag_mac=parsed.mac_tag,
                esp_mac=parsed.mac_esp,
                rssi=parsed.rssi,
                raw_packet=parsed.raw_packet,
                rx_ctrl=parsed.rx_ctrl,
                timestamp=datetime.now(timezone.utc),
                session=session,
            )
    except Exception as e:
        logger.error("Failed to save packet to DB: %s", e)


async def _listen_channel(channel: int, host: str, port: int, grouper: BeaconGrouper) -> None:
    while True:
        writer = None
        try:
            logger.debug("Channel %d: connecting to %s:%d", channel, host, port)
            reader, writer = await asyncio.open_connection(host, port)
            logger.info("Channel %d: connected to %s:%d", channel, host, port)

            while True:
                line = await reader.readline()
                if not line:
                    logger.warning("Channel %d: connection closed by remote.", channel)
                    break

                parsed = parse_packet(line)
                if parsed is None:
                    continue

                parsed.received_at = time.monotonic()

                # Persist asynchronously in a thread pool
                asyncio.create_task(asyncio.to_thread(_store_packet_sync, parsed))

                # Broadcast raw packet to WebSocket packet-channel subscribers
                asyncio.create_task(
                    publish_packet({
                        "tag_mac": parsed.mac_tag,
                        "esp_mac": parsed.mac_esp,
                        "rssi": parsed.rssi,
                        "seq": parsed.seq,
                        "received_at": parsed.received_at,
                    })
                )

                await grouper.add_packet(parsed)
                logger.debug(
                    "Channel %d: queued tag=%s seq=%d rssi=%d",
                    channel, parsed.mac_tag, parsed.seq, parsed.rssi,
                )

        except (ConnectionRefusedError, OSError) as exc:
            logger.error(
                "Channel %d: network error — %s. Retrying in %.1fs",
                channel, exc, settings.reconnect_delay,
            )
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


async def start_ethernet_listeners(grouper: BeaconGrouper) -> list[asyncio.Task]:
    tasks: list[asyncio.Task] = []
    for channel, port in CHANNEL_PORTS.items():
        task = asyncio.create_task(
            _listen_channel(channel, settings.esp_host, port, grouper),
            name=f"ethernet-listener-ch{channel}",
        )
        tasks.append(task)
        logger.info("Channel %d: background task created (port %d).", channel, port)
    return tasks
