from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class TimestampValue(BaseModel):
    timestamp: datetime
    value: float
