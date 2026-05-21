from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BackupStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    source_device = Column(String(256), nullable=True)
    file_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    status = Column(SQLEnum(BackupStatus), default=BackupStatus.in_progress)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id", ondelete="SET NULL"), nullable=True)
    storage_path = Column(String(512), nullable=True)

    client = relationship("Client", back_populates="backup_records")
    storage = relationship("Storage")
