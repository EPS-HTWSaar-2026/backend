from dataclasses import dataclass
from typing import Optional


_MIN_PACKET_LEN = 29


def _format_mac(raw_bytes: bytes) -> str:
    return ":".join(f"{b:02X}" for b in raw_bytes)


def _parse_rssi(raw_bytes: bytes) -> int:
    value = raw_bytes[0]
    return value if value < 128 else value - 256


@dataclass
class ParsedPacket:
    mac_tag: str    
    mac_esp: str   
    rssi: int     


def parse_packet(raw: bytes) -> Optional[ParsedPacket]:
    """
    Parse a raw bytes packet and return a ParsedPacket, or None on failure.

    The caller is responsible for logging / discarding None results.
    """
    if len(raw) < _MIN_PACKET_LEN:
        return None

    try:
        tag_bytes = raw[7:13]       
        rssi_byte = raw[20:21]     
        esp_bytes = raw[23:26]    

        mac_tag = _format_mac(tag_bytes)
        mac_esp = _format_mac(esp_bytes)
        rssi = _parse_rssi(rssi_byte)

        return ParsedPacket(mac_tag=mac_tag, mac_esp=mac_esp, rssi=rssi)

    except (IndexError, ValueError):
        return None
