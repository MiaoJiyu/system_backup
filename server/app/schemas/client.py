from pydantic import BaseModel, Field
from datetime import datetime
from app.models.client import ClientStatus


class ClientUpdate(BaseModel):
    group_id: int | None = None
    tags: list[str] | None = None
    user_id: int | None = None


class ClientResponse(BaseModel):
    id: int
    uuid: str
    ip_address: str | None = None
    user_id: int | None = None
    group_id: int | None = None
    tags: list = []
    status: str = "offline"
    last_seen: datetime | None = None
    os_version: str | None = None
    client_version: str | None = None
    config_status: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CommandRequest(BaseModel):
    command: str
    payload: dict | None = None


class CredentialRequest(BaseModel):
    storage_id: int
    path: str
    file_size: int = 0


class ClientConfigRequest(BaseModel):
    """Override config fields to push to a specific client."""
    config: dict = Field(default_factory=dict)
    policy_template_id: int | None = None
