import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from .parser import ParsedPacket

logger = logging.getLogger(__name__)

GROUPING_WINDOW = 0.15
MIN_LISTENERS = 3


@dataclass
class PacketGroup:
    tag_mac: str
    packets: dict = field(default_factory=dict)
    deadline: float = 0.0


class BeaconGrouper:
    def __init__(self, on_group_ready: Callable[[list[ParsedPacket]], Awaitable[None]]):
        self._on_ready = on_group_ready
        self._groups: dict[str, PacketGroup] = {}
        self._lock = asyncio.Lock()

    def _make_key(self, packet: ParsedPacket) -> str:
        return f"{packet.mac_tag}:{packet.seq}"

    async def add_packet(self, packet: ParsedPacket) -> None:
        async with self._lock:
            key = self._make_key(packet)

            if key not in self._groups:
                self._groups[key] = PacketGroup(
                    tag_mac=packet.mac_tag,
                    deadline=time.monotonic() + GROUPING_WINDOW,
                )

            group = self._groups[key]
            existing = group.packets.get(packet.mac_esp)
            if existing is None or packet.rssi > existing.rssi:
                group.packets[packet.mac_esp] = packet

    async def flush_loop(self) -> None:
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            async with self._lock:
                expired = [k for k, g in self._groups.items() if now >= g.deadline]
                for key in expired:
                    group = self._groups.pop(key)
                    if len(group.packets) >= MIN_LISTENERS:
                        asyncio.get_event_loop().create_task(
                            self._on_ready(list(group.packets.values()))
                        )
                        logger.debug("Group created -> send for calculation")
                    else:
                        logger.debug(
                            "Discarded group %s — only %d listener(s) heard it",
                            key, len(group.packets)
                        )