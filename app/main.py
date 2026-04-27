from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .routers import ingest, status, tags, events


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="RTLS Monitoring Backend",
    description="Backend for ESP32-based tag monitoring and visualization",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(status.router)
app.include_router(tags.router)
app.include_router(events.router)
app.include_router(esp_config.router)

@app.get("/")
def root():
    return {
        "message": "RTLS Monitoring Backend is running",
        "docs": "/docs",
    }
