from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


class ComponentHealthResponse(BaseModel):
    status: str
    component: str
    message: str