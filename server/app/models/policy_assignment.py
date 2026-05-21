from sqlalchemy import Column, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class GroupPolicy(Base):
    __tablename__ = "group_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    policy_template_id = Column(Integer, ForeignKey("policy_templates.id", ondelete="CASCADE"), nullable=False)

    group = relationship("Group", back_populates="group_policies")
    policy_template = relationship("PolicyTemplate", back_populates="group_policies")


class TagPolicy(Base):
    __tablename__ = "tag_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    policy_template_id = Column(Integer, ForeignKey("policy_templates.id", ondelete="CASCADE"), nullable=False)
    priority = Column(Integer, default=0)

    tag = relationship("Tag", back_populates="tag_policies")
    policy_template = relationship("PolicyTemplate", back_populates="tag_policies")


class ClientPolicyOverride(Base):
    __tablename__ = "client_policy_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False)
    policy_template_id = Column(Integer, ForeignKey("policy_templates.id", ondelete="SET NULL"), nullable=True)
    override_config = Column(JSON, nullable=True)

    policy_template = relationship("PolicyTemplate", back_populates="client_overrides")
    client = relationship("Client", back_populates="policy_override", uselist=False)
