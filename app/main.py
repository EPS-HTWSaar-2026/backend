import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .ethernet.cal import on_group_ready
from .ethernet.grouper import BeaconGrouper
from .ethernet.listener import start_ethernet_listeners
from .routers import listeners, packets, tags
from .websocket import start_websockets

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    grouper = BeaconGrouper(on_group_ready=on_group_ready)

    app.state.ethernet_tasks = await start_ethernet_listeners(grouper)
    app.state.grouper_task = asyncio.create_task(
        grouper.flush_loop(), name="beacon-grouper-flush"
    )
    app.state.ws_task = asyncio.create_task(
        start_websockets(), name="websocket-server"
    )

    yield

    # Graceful shutdown — cancel every background task and wait for them
    all_tasks = [
        *app.state.ethernet_tasks,
        app.state.grouper_task,
        app.state.ws_task,
    ]
    for task in all_tasks:
        task.cancel()

    await asyncio.gather(*all_tasks, return_exceptions=True)


app = FastAPI(
    title="RTLS Monitoring Backend",
    description="Backend for ESP32-based tag monitoring and visualization",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tags.router)
app.include_router(listeners.router)
app.include_router(packets.router)


@app.get("/", tags=["health"])
def root():
    return {
        "message": "RTLS Monitoring Backend is running",
        "version": app.version,
        "docs": "/docs",
    }
