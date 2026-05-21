from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Enum as SQLEnum, func
from app.database import Base
import enum


class StorageType(str, enum.Enum):
    local = "local"
    s3 = "s3"
    sftp = "sftp"


class Storage(Base):
    __tablename__ = "storages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    type = Column(SQLEnum(StorageType), nullable=False)
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
