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
<<<<<<< HEAD
<<<<<<< HEAD
    allow_origins=["*"],
=======
=======
>>>>>>> 03ee70d403d3e9d0ac3128b2e1f6ea79f7d38524
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # desarrollo
<<<<<<< HEAD
>>>>>>> 62f932a (Backend new)
=======
>>>>>>> 03ee70d403d3e9d0ac3128b2e1f6ea79f7d38524
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(status.router)
app.include_router(tags.router)
app.include_router(events.router)


@app.get("/")
def root():
    return {
        "message": "RTLS Monitoring Backend is running",
        "docs": "/docs",
    }