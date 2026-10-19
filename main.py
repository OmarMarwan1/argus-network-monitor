from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import devices, metrics, alerts, predictions
from schemas import DeviceOut, MetricOut, AlertsOut, PredictionsOut, DeviceCreate, DeviceUpdate
from typing import List

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Network Monitoring API is running"}


@app.get("/devices", response_model=List[DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    Devices = db.query(devices).all()
    return Devices


@app.get("/devices/{id}", response_model=DeviceOut)
def get_device_by_id(id: int, db: Session = Depends(get_db)):
    Devices = db.query(devices).filter(devices.device_id == id).first()
    if Devices:
        return Devices
    else:
        raise HTTPException(status_code=404, detail="no device found")


@app.get("/devices/{id}/metrics", response_model=List[MetricOut])
def get_metric_by_id(id: int, db: Session = Depends(get_db)):
    Metrics = db.query(metrics).filter(metrics.device_id == id).order_by(
        metrics.timestamp.desc()).limit(100).all()
    if Metrics:
        return Metrics
    else:
        raise HTTPException(status_code=404, detail="no metric found")


@app.get("/alerts", response_model=List[AlertsOut])
def get_alerts(severity: str = None, db: Session = Depends(get_db)):
    Alerts = db.query(alerts)
    if severity:
        Alerts = Alerts.filter(alerts.severity == severity)
    return Alerts.all()


@app.get("/predictions", response_model=List[PredictionsOut])
def get_predictions(db: Session = Depends(get_db)):
    Predictions = db.query(predictions).all()
    return Predictions


@app.post("/add_device", response_model=DeviceOut)
def add_device(device: DeviceCreate, db: Session = Depends(get_db)):
    new_device = devices(**device.model_dump())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@app.patch("/devices/{id}", response_model=DeviceOut)
def update_device(id: int, updates: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(devices).filter(devices.device_id == id).first()

    if not device:
        raise HTTPException(status_code=404, detail="no device found")

    updates_dict = updates.model_dump(exclude_unset=True)
    for key, value in updates_dict.items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)
    return device
