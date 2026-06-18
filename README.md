# RTLS Monitoring Backend

FastAPI backend for an ESP32-based Real-Time Location System. Receives WIFI tag detections over TCP from ESP32 anchors, computes tag positions via trilateration, and streams results over WebSocket.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the example env file and edit it:

```bash
cp .env.example .env
```

Then start the server:

```bash
uvicorn app.main:app --reload
```

API docs are available at **http://\<your-ip\>:8000/docs**

---

## .env

| Variable          | Example         | Description                              |
|-------------------|-----------------|------------------------------------------|
| `IP`              | `192.168.1.50`  | IP this machine listens on (WebSocket)   |
| `ESP_HOST`        | `192.168.1.100` | IP address of the ESP32 host             |
| `ESP_PORT_1`      | `4001`          | TCP port for ESP32 channel 1             |
| `ESP_PORT_2`      | `4002`          | TCP port for ESP32 channel 2             |
| `ESP_PORT_3`      | `4003`          | TCP port for ESP32 channel 3             |
| `RECONNECT_DELAY` | `5.0`           | Seconds to wait before reconnect attempt |

**.env.example**

```env
IP=192.168.1.50
ESP_HOST=192.168.1.100
ESP_PORT_1=4001
ESP_PORT_2=4002
ESP_PORT_3=4003
RECONNECT_DELAY=5.0
```

---

## Ports

| Port   | Protocol  | Purpose                        |
|--------|-----------|--------------------------------|
| `8000` | HTTP      | REST API + Swagger UI (`/docs`)|
| `8765` | WebSocket | Live location & packet stream  |
| `4001` | TCP       | ESP32 channel 1 (outbound)     |
| `4002` | TCP       | ESP32 channel 2 (outbound)     |
| `4003` | TCP       | ESP32 channel 3 (outbound)     |

---

## API

| Method | Path                    | Description                        |
|--------|-------------------------|------------------------------------|
| GET    | `/api/tags`             | All known tags with last position  |
| GET    | `/api/tags/{mac}`       | Single tag                         |
| PATCH  | `/api/tags/{mac}`       | Manually override tag position     |
| DELETE | `/api/tags/{mac}`       | Remove tag                         |
| GET    | `/api/listeners`        | All listeners (anchors)            |
| POST   | `/api/listeners`        | Add / update a listener            |
| PATCH  | `/api/listeners/{mac}`  | Update calibration or position     |
| DELETE | `/api/listeners/{mac}`  | Remove listener                    |
| GET    | `/api/packets`          | Recent raw packets                 |
| GET    | `/docs`                 | Swagger UI                         |

## WebSocket

Connect to `ws://<ip>:8765` and send a subscription message:

```json
{ "subscribe": "locations" }
```

or

```json
{ "subscribe": "packets" }
```

`locations` streams trilaterated tag positions. `packets` streams raw WIFI packets detections as they arrive.
