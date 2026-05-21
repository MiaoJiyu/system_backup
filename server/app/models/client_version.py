from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ClientVersion(Base):
    __tablename__ = "client_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(32), unique=True, nullable=False, index=True)
    file_name = Column(String(128), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    download_url = Column(String(512), nullable=True)
    mirror_url = Column(String(512), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changelog = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    uploader = relationship("User")
