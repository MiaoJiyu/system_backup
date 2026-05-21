from pydantic import BaseModel, Field
from datetime import datetime
from app.models.policy_template import ScheduleType, VersionUpdatePolicy


class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    backup_directories: list[str] = []
    backup_usb: bool = True
    incremental: bool = True
    backup_meta_log: bool = True
    schedule_type: ScheduleType = ScheduleType.manual
    schedule_config: dict | None = None
    upload_storage_id: int | None = None
    server_address: str | None = None
    server_port: int | None = None
    encryption_enabled: bool = True
    compression_enabled: bool = True
    version_update_policy: VersionUpdatePolicy = VersionUpdatePolicy.after_task


class PolicyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = None
    backup_directories: list[str] | None = None
    backup_usb: bool | None = None
    incremental: bool | None = None
    backup_meta_log: bool | None = None
    schedule_type: ScheduleType | None = None
    schedule_config: dict | None = None
    upload_storage_id: int | None = None
    server_address: str | None = None
    server_port: int | None = None
    encryption_enabled: bool | None = None
    compression_enabled: bool | None = None
    version_update_policy: VersionUpdatePolicy | None = None


class PolicyResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    backup_directories: list = []
    backup_usb: bool = True
    incremental: bool = True
    backup_meta_log: bool = True
    schedule_type: str = "manual"
    schedule_config: dict | None = None
    upload_storage_id: int | None = None
    server_address: str | None = None
    server_port: int | None = None
    encryption_enabled: bool = True
    compression_enabled: bool = True
    version_update_policy: str = "after_task"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PolicyAssignRequest(BaseModel):
    policy_template_id: int
    group_id: int | None = None
    tag_id: int | None = None
    client_id: int | None = None
    priority: int = 0
    override_config: dict | None = None
