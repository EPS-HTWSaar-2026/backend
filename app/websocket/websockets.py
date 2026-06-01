import asyncio
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosed

from ..config import settings

logger = logging.getLogger(__name__)

# Two independent subscriber sets — one per channel.
_LOCATION_VIEWERS: set[websockets.ServerConnection] = set()
_PACKET_VIEWERS: set[websockets.ServerConnection] = set()

_CHANNELS = {
    "locations": _LOCATION_VIEWERS,
    "packets": _PACKET_VIEWERS,
}

# ── Handlers ────────────────────────────────────────────────────────────────

async def _handler(websocket: websockets.ServerConnection) -> None:
    """
    Clients select a channel by sending a JSON subscription message:

        {"subscribe": "locations"}   — real-time tag positions
        {"subscribe": "packets"}     — raw packet arrivals

    The connection is dropped if no valid subscription arrives within 5 s,
    or immediately if an unknown channel is requested.
    """
    peer = websocket.remote_address
    logger.debug("WS connection from %s", peer)

    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        msg = json.loads(raw)
        channel = msg.get("subscribe", "")
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
        await websocket.close(1008, "Expected JSON subscription message")
        logger.warning("WS %s: bad or missing subscription — closed", peer)
        return

    viewers = _CHANNELS.get(channel)
    if viewers is None:
        await websocket.close(1008, f"Unknown channel '{channel}'")
        logger.warning("WS %s: unknown channel '%s' — closed", peer, channel)
        return

    viewers.add(websocket)
    logger.info("WS %s subscribed to '%s' (total: %d)", peer, channel, len(viewers))

    try:
        await websocket.wait_closed()
    except ConnectionClosed:
        pass
    finally:
        viewers.discard(websocket)
        logger.info("WS %s unsubscribed from '%s' (total: %d)", peer, channel, len(viewers))


# ── Public publish helpers ───────────────────────────────────────────────────

async def publish_location(payload: dict) -> None:
    """Broadcast a trilaterated position to all location-channel subscribers."""
    if _LOCATION_VIEWERS:
        data = json.dumps(payload)
        websockets.broadcast(_LOCATION_VIEWERS, data)
        logger.debug("location → %s", data)


async def publish_packet(payload: dict) -> None:
    """Broadcast a raw packet arrival to all packet-channel subscribers."""
    if _PACKET_VIEWERS:
        data = json.dumps(payload)
        websockets.broadcast(_PACKET_VIEWERS, data)
        logger.debug("packet → %s", data)


# ── Legacy alias kept for any callers that used `publish` directly ───────────
async def publish(payload: dict) -> None:
    await publish_location(payload)


# ── Server lifecycle ─────────────────────────────────────────────────────────

async def start_websockets() -> None:
    """Start the WebSocket server and block until cancelled."""
    async with websockets.serve(_handler, settings.ip, 8765):
        logger.info("WebSocket server running on ws://%s:8765", settings.ip)
        await asyncio.Future()  # run forever
