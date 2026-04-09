"""Database models for automation workflows and tasks in SIGMA-OS."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base


class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # JSON string describing steps/automation definition
    config = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("AutomationTask", back_populates="workflow", cascade="all, delete-orphan")


class AutomationTask(Base):
    __tablename__ = "automation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("automation_workflows.id"), nullable=False)

    # high-level state, e.g. pending/running/success/failed
    status = Column(String(50), default="pending", index=True)

    # command that will be sent to agents
    command = Column(Text, nullable=False)

    # raw result text or JSON (stringified)
    result = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    workflow = relationship("AutomationWorkflow", back_populates="tasks")
