import logging
import asyncio
import websockets
import json
from ..config import settings

logger = logging.getLogger(__name__)
VIEWERS = set()

async def handler(websocket):
    VIEWERS.add(websocket)
    logger.debug("Client connected")
    try:
        await websocket.wait_closed()
    finally:
        VIEWERS.discard(websocket)
        logger.debug("Client disconnected")

async def publish(location):
    if VIEWERS:
        payload = json.dumps(location)
        websockets.broadcast(VIEWERS, payload)
        logger.debug(f"Published → {payload}")

async def start_websockets():
    async with websockets.serve(handler, settings.ip, 8765):
        logger.debug(f"Server running on ws://{settings.ip}:8765")
        await asyncio.Future()