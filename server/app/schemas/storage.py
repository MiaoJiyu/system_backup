from pydantic import BaseModel, Field
from datetime import datetime
from app.models.storage import StorageType


class StorageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    type: StorageType
    config: dict
    enabled: bool = True


class StorageUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    type: StorageType | None = None
    config: dict | None = None
    enabled: bool | None = None


class StorageResponse(BaseModel):
    id: int
    name: str
    type: str
    config: dict
    enabled: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
