import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .parser import ParsedPacket

logger = logging.getLogger(__name__)

GROUPING_WINDOW = 0.15  # seconds — how long a bucket stays open
MIN_LISTENERS = 3
MAX_BUCKET_AGE = 2.0    # drop buckets older than this even if underfull


@dataclass
class TimeBucket:
    open_time: float
    deadline: float 
    packets: dict[str, ParsedPacket] = field(
        default_factory=dict
    )


class BeaconGrouper:
    def __init__(
        self, on_group_ready: Callable[[list[ParsedPacket]], Awaitable[None]]
    ):
        self._on_ready = on_group_ready
        self._buckets: dict[str, TimeBucket] = {} 
        self._lock = asyncio.Lock()

    async def add_packet(self, packet: ParsedPacket) -> None:
        async with self._lock:
            now = time.monotonic()
            tag = packet.mac_tag
            bucket = self._buckets.get(tag)

            # Start a new bucket if none exists or the current one has expired
            if bucket is None or now >= bucket.deadline:
                if bucket is not None and len(bucket.packets) >= MIN_LISTENERS:
                    # Flush the expiring bucket before opening a new one
                    asyncio.ensure_future(
                        self._on_ready(list(bucket.packets.values()))
                    )
                    logger.debug("Group flushed early for tag %s", tag)

                bucket = TimeBucket(
                    open_time=now,
                    deadline=now + GROUPING_WINDOW,
                )
                self._buckets[tag] = bucket

            # Keep the best RSSI reading per listener
            existing = bucket.packets.get(packet.mac_esp)
            if existing is None or packet.rssi > existing.rssi:
                bucket.packets[packet.mac_esp] = packet

    async def flush_loop(self) -> None:
        """Periodic flush: drain every bucket whose deadline has passed."""
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            async with self._lock:
                expired = [
                    tag for tag, b in self._buckets.items() if now >= b.deadline
                ]
                for tag in expired:
                    bucket = self._buckets.pop(tag)
                    if len(bucket.packets) >= MIN_LISTENERS:
                        asyncio.ensure_future(
                            self._on_ready(list(bucket.packets.values()))
                        )
                        logger.debug(
                            "Group flushed for tag %s (%d listeners)",
                            tag, len(bucket.packets),
                        )
                    else:
                        logger.debug(
                            "Discarded bucket for %s — only %d listener(s) (age=%.3fs)",
                            tag,
                            len(bucket.packets),
                            now - bucket.open_time,
                        )
