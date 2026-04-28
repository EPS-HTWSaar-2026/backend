import asyncio
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlmodel import Session

from ..database import engine
from ..schemas import IngestPayload
from ..services import ingest_payload
from .parser import parse_packet

load_dotenv()

logger = logging.getLogger(__name__)


ESP_HOST: str = os.getenv("ESP_HOST", "192.168.1.100")

CHANNEL_PORTS: dict[int, int] = {
    1: int(os.getenv("ESP_PORT_1", "4001")),
    2: int(os.getenv("ESP_PORT_2", "4002")),
    3: int(os.getenv("ESP_PORT_3", "4003")),
}

RECONNECT_DELAY: float = 5.0

READ_BUFFER: int = 512


def _save_packet(mac_tag: str, mac_esp: str, rssi: int, channel: int) -> None:
    payload = IngestPayload(
        tag_id=mac_tag,
        event="detected",
        rssi=rssi,
        channel=channel,
        source=mac_esp,
        timestamp=datetime.now(timezone.utc),
    )
    with Session(engine) as session:
        ingest_payload(payload, session)



async def _listen_channel(channel: int, host: str, port: int) -> None:
    logger.info("Channel %d: starting listener → %s:%d", channel, host, port)

    while True:
        reader: asyncio.StreamReader | None = None
        writer: asyncio.StreamWriter | None = None

        try:
            logger.info("Channel %d: connecting to %s:%d …", channel, host, port)
            reader, writer = await asyncio.open_connection(host, port)
            logger.info("Channel %d: connected.", channel)

            buf = bytearray()

            while True:
                chunk = await reader.read(READ_BUFFER)

                if not chunk:
                    # Remote closed the connection
                    logger.warning("Channel %d: connection closed by remote.", channel)
                    break

                buf.extend(chunk)

                # A packet may arrive fragmented; accumulate until we have enough bytes
                while len(buf) >= 29:
                    raw = bytes(buf[:29])
                    parsed = parse_packet(raw)

                    if parsed is None:
                        # Bad packet — discard one byte and try to re-sync
                        logger.debug(
                            "Channel %d: failed to parse packet, re-syncing. raw=%s",
                            channel,
                            raw.hex(),
                        )
                        buf = buf[1:]
                        continue

                    # Good packet — consume it and persist
                    buf = buf[29:]

                    try:
                        _save_packet(
                            mac_tag=parsed.mac_tag,
                            mac_esp=parsed.mac_esp,
                            rssi=parsed.rssi,
                            channel=channel,
                        )
                        logger.debug(
                            "Channel %d: saved tag=%s rssi=%d",
                            channel,
                            parsed.mac_tag,
                            parsed.rssi,
                        )
                    except Exception:
                        logger.exception(
                            "Channel %d: database error for tag %s",
                            channel,
                            parsed.mac_tag,
                        )

        except (ConnectionRefusedError, OSError) as exc:
            logger.error(
                "Channel %d: network error – %s. Retrying in %.0fs …",
                channel,
                exc,
                RECONNECT_DELAY,
            )
        except Exception:
            logger.exception("Channel %d: unexpected error. Retrying …", channel)

        finally:
            if writer is not None:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        await asyncio.sleep(RECONNECT_DELAY)


async def start_ethernet_listeners() -> list[asyncio.Task]:
    tasks: list[asyncio.Task] = []
    for channel, port in CHANNEL_PORTS.items():
        task = asyncio.create_task(
            _listen_channel(channel, ESP_HOST, port),
            name=f"ethernet-listener-ch{channel}",
        )
        tasks.append(task)
        logger.info("Channel %d: background task created (port %d).", channel, port)
    return tasks
