from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    parent_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("Group", remote_side=[id], backref="children")
    clients = relationship("Client", back_populates="group")
    group_policies = relationship("GroupPolicy", back_populates="group", cascade="all, delete-orphan")
