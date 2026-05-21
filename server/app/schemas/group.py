from pydantic import BaseModel, Field
from datetime import datetime


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    parent_id: int | None = None
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    parent_id: int | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
