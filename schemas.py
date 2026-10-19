from pydantic import BaseModel
from datetime import datetime


class DeviceOut(BaseModel):
    device_id: int
    name: str
    device_type: str
    layer: str | None = None
    status: str

    class Config:
        from_attributes = True


class MetricOut(BaseModel):
    metrics_id: int
    device_id: int
    timestamp: datetime
    cpu: float
    memory: float
    temperature: float
    latency: float
    packet_loss: float
    traffic: float
    interface_errors: int

    class Config:
        from_attributes = True


class AlertsOut(BaseModel):
    alert_id: int
    device_id: int
    timestamp: datetime
    alert_type: str
    metric: str
    severity: str
    description: str | None = None

    class Config:
        from_attributes = True


class PredictionsOut(BaseModel):
    prediction_id: int
    device_id: int
    timestamp: datetime
    failure_risk: float
    risk_level: str
    explanation: str | None = None

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    layer: str | None = None
    ip_add: str | None = None
    status: str = "online"


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    layer: str | None = None
    ip_add: str | None = None
    status: str | None = None
