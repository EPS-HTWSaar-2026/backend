import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from .parser import ParsedPacket

logger = logging.getLogger(__name__)

GROUPING_WINDOW = 0.15   # seconds — how long a bucket stays open
MIN_LISTENERS = 3
MAX_BUCKET_AGE = 2.0     # drop buckets older than this even if underfull


@dataclass
class TimeBucket:
    open_time: float                        # monotonic time this bucket was created
    deadline: float                         # when to flush it
    packets: dict[str, ParsedPacket] = field(default_factory=dict)  # mac_esp → best packet


class BeaconGrouper:
    def __init__(self, on_group_ready: Callable[[list[ParsedPacket]], Awaitable[None]]):
        self._on_ready = on_group_ready
        # One active bucket per tag MAC
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
                    # Flush the previous bucket immediately before opening a new one
                    asyncio.get_event_loop().create_task(
                        self._on_ready(list(bucket.packets.values()))
                    )
                    logger.debug("Group created -> send for calculation (early flush)")
                bucket = TimeBucket(
                    open_time=now,
                    deadline=now + GROUPING_WINDOW,
                )
                self._buckets[tag] = bucket

            # Keep the best RSSI reading per ESP
            existing = bucket.packets.get(packet.mac_esp)
            if existing is None or packet.rssi > existing.rssi:
                bucket.packets[packet.mac_esp] = packet

    async def flush_loop(self) -> None:
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            async with self._lock:
                tags_to_flush = [
                    tag for tag, b in self._buckets.items()
                    if now >= b.deadline
                ]
                for tag in tags_to_flush:
                    bucket = self._buckets.pop(tag)
                    if len(bucket.packets) >= MIN_LISTENERS:
                        asyncio.get_event_loop().create_task(
                            self._on_ready(list(bucket.packets.values()))
                        )
                        logger.debug("Group created -> send for calculation")
                    else:
                        logger.debug(
                            "Discarded bucket for %s — only %d listener(s) (age=%.3fs)",
                            tag, len(bucket.packets), now - bucket.open_time
                        )
