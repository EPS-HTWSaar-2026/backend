# RTLS Monitoring Backend

FastAPI backend for an ESP32-based Real-Time Location System (RTLS). Receives BLE tag detections over Ethernet from ESP32 anchors, persists them, and exposes a REST API for monitoring.

## Architecture

- **Ethernet listeners** — persistent async TCP connections to ESP32 anchors on configurable ports; parse raw 29-byte packets and ingest detections
- **Ingest service** — upserts tag state and appends events to SQLite via SQLModel
- **REST API** — `/api/tags`, `/api/events`, `/api/status`, `/api/ingest`

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit as needed
uvicorn app.main:app --reload
```

## Environment Variables

| Variable      | Default         | Description                        |
|---------------|-----------------|------------------------------------|
| `ESP_HOST`    | `192.168.1.100` | IP address of the ESP32 host       |
| `ESP_PORT_1`  | `4001`          | TCP port for channel 1             |
| `ESP_PORT_2`  | `4002`          | TCP port for channel 2             |
| `ESP_PORT_3`  | `4003`          | TCP port for channel 3             |

## API

| Method | Path            | Description                        |
|--------|-----------------|------------------------------------|
| GET    | `/api/tags`     | All tags with live-computed status |
| GET    | `/api/events`   | Recent events (default 50)         |
| GET    | `/api/status`   | ESP32 connectivity + tag count     |
| POST   | `/api/ingest`   | Manual payload ingest              |
| GET    | `/docs`         | Swagger UI                         |