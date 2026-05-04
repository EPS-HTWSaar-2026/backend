import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


def _format_mac(raw: str) -> str:
    clean = raw.replace(":", "").upper()
    return ":".join(clean[i:i + 2] for i in range(0, 12, 2))


@dataclass
class ParsedPacket:
    mac_tag: str
    mac_esp: str
    rssi: int
    seq: int
    received_at: float = field(default=0.0)


def parse_packet(raw: bytes) -> Optional[ParsedPacket]:
    try:
        text = raw.decode("ascii", errors="ignore").strip()
        data = json.loads(text)

        return ParsedPacket(
            mac_tag=_format_mac(data["tAddr"]),
            mac_esp=_format_mac(data["esp_mac"]),
            rssi=int(data["rssi"]),
            seq=int(data["seq"]),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse packet as JSON: {raw}. Error: {e}")
        return None