import asyncio
import websockets
import json

VIEWERS = set()

async def handler(websocket): # websocket -> represents connection to the client
    VIEWERS.add(websocket)
    print("Client connected")
    try:
        await websocket.wait_closed()
    finally:
        VIEWERS.discard(websocket)
        print("Client disconnected")

async def publish(location):
    if VIEWERS:
        payload = json.dumps(location) # location data ->  JSON string
        websockets.broadcast(VIEWERS, payload) # Send payload to all connected clients
        print(f"Published → {payload}")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")

        asyncio.create_task(simulate_location_updates())
        await asyncio.Future()

# Simulation of data
async def simulate_location_updates():
    while True:
        location = {"latitude": 40.7128, "longitude": -74.0060} 
        await publish(location)
        await asyncio.sleep(5)

asyncio.run(main())