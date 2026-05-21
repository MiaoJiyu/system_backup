from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class ClientLog(Base):
    __tablename__ = "client_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    level = Column(SQLEnum(LogLevel), nullable=False, default=LogLevel.INFO)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    client = relationship("Client", back_populates="logs")

    __table_args__ = (
        Index("ix_client_logs_client_created", "client_id", "created_at"),
    )
