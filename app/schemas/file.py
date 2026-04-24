from pydantic import BaseModel
from datetime import datetime


class FileResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    content_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True
