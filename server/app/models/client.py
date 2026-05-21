from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ClientStatus(str, enum.Enum):
    online = "online"
    offline = "offline"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(64), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    status = Column(SQLEnum(ClientStatus), default=ClientStatus.offline)
    last_seen = Column(DateTime, nullable=True)
    os_version = Column(String(128), nullable=True)
    client_version = Column(String(32), nullable=True)
    config_status = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="clients")
    group = relationship("Group", back_populates="clients")
    policy_override = relationship("ClientPolicyOverride", back_populates="client", uselist=False, cascade="all, delete-orphan")
    backup_records = relationship("BackupRecord", back_populates="client", cascade="all, delete-orphan")
    logs = relationship("ClientLog", back_populates="client", cascade="all, delete-orphan")
