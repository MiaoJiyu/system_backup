from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ScheduleType(str, enum.Enum):
    cron = "cron"
    interval = "interval"
    manual = "manual"


class VersionUpdatePolicy(str, enum.Enum):
    force = "force"
    after_task = "after_task"
    idle = "idle"


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    backup_directories = Column(JSON, nullable=True, default=list)
    backup_usb = Column(Boolean, default=True)
    incremental = Column(Boolean, default=True)
    backup_meta_log = Column(Boolean, default=True)
    schedule_type = Column(SQLEnum(ScheduleType), default=ScheduleType.manual)
    schedule_config = Column(JSON, nullable=True)
    upload_storage_id = Column(Integer, ForeignKey("storages.id", ondelete="SET NULL"), nullable=True)
    server_address = Column(String(256), nullable=True)
    server_port = Column(Integer, nullable=True)
    encryption_enabled = Column(Boolean, default=True)
    compression_enabled = Column(Boolean, default=True)
    version_update_policy = Column(SQLEnum(VersionUpdatePolicy), default=VersionUpdatePolicy.after_task)
    created_at = Column(DateTime, server_default=func.now())

    upload_storage = relationship("Storage", backref="policy_templates")
    group_policies = relationship("GroupPolicy", back_populates="policy_template", cascade="all, delete-orphan")
    tag_policies = relationship("TagPolicy", back_populates="policy_template", cascade="all, delete-orphan")
    client_overrides = relationship("ClientPolicyOverride", back_populates="policy_template", cascade="all, delete-orphan")
