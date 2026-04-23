from fastapi import FastAPI
from database import engine, SessionLocal
from models import Tag, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/data")
def receive_data(data: dict):
    db = SessionLocal()

    mac = data.get("mac")
    rssi = data.get("rssi")

    new_tag = Tag(mac=mac, rssi=rssi)

    db.add(new_tag)
    db.commit()

    db.close()

    return {"status": "saved"}

@app.get("/tags")
def get_tags():
    db = SessionLocal()

    tags = db.query(Tag).all()

    result = []
    for t in tags:
        result.append({
            "id": t.id,
            "mac": t.mac,
            "rssi": t.rssi
        })

    db.close()

    return result