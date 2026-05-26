import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

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
    raw_packet: str
    rx_ctrl: Dict[str, Any]
    received_at: float = 0.0


def parse_packet(raw: bytes) -> Optional[ParsedPacket]:
    try:
        text = raw.decode("ascii", errors="ignore").strip()
        data = json.loads(text)

        raw_hex = data.get("raw_packets")
        if not raw_hex:
            raise ValueError("Missing 'raw_packets' in payload")
            
        raw_bytes = bytes.fromhex(raw_hex)
        if len(raw_bytes) < 24:
            raise ValueError("Packet too short to parse 802.11 header")

        # Address 2 (Source/Tag MAC) is bytes 10 to 15
        mac_tag_bytes = raw_bytes[10:16]
        mac_tag = mac_tag_bytes.hex()

        # Sequence control is bytes 22 to 23
        seq_ctrl = int.from_bytes(raw_bytes[22:24], byteorder="little")
        seq = seq_ctrl >> 4

        mac_esp = data["espMac"]
        rx_ctrl = data.get("rx_ctrl", {})
        rssi = rx_ctrl.get("rssi", 0)

        return ParsedPacket(
            mac_tag=_format_mac(mac_tag),
            mac_esp=_format_mac(mac_esp),
            rssi=int(rssi),
            seq=seq,
            raw_packet=raw_hex,
            rx_ctrl=rx_ctrl,
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse packet as JSON: {raw}. Error: {e}")
        return None
