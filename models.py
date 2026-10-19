from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from database import Base


class devices(Base):
    __tablename__ = "devices"
    device_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    device_type = Column(String)
    layer = Column(String)
    ip_add = Column(String)
    status = Column(String)
    created_at = Column(DateTime)


class metrics(Base):
    __tablename__ = "metrics"
    metrics_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    timestamp = Column(DateTime)
    cpu = Column(Float)
    memory = Column(Float)
    temperature = Column(Float)
    latency = Column(Float)
    packet_loss = Column(Float)
    traffic = Column(Float)
    interface_errors = Column(Integer)


class alerts(Base):
    __tablename__ = "alerts"
    alert_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    timestamp = Column(DateTime)
    alert_type = Column(String)
    metric = Column(String)
    severity = Column(String)
    description = Column(String)


class predictions(Base):
    __tablename__ = "predictions"
    prediction_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    timestamp = Column(DateTime)
    failure_risk = Column(Float)
    risk_level = Column(String)
    explanation = Column(String)
