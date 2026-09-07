from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    RECEIVED = "received"
    INVESTIGATING = "investigating"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class IncidentInput(BaseModel):
    line_id: str = Field(min_length=1, examples=["PACK-03"])
    description: str = Field(min_length=10)
    output_drop_pct: float | None = Field(default=None, ge=0, le=100)


class PlanStep(BaseModel):
    id: str
    agent: str
    tool: str
    purpose: str


class IncidentPlan(BaseModel):
    objective: str
    steps: list[PlanStep]
    requires_human_approval: bool = True


class ToolEvidence(BaseModel):
    tool: str
    data: dict[str, Any]


class ActionProposal(BaseModel):
    action_type: str
    reason: str
    payload: dict[str, Any]
    requires_approval: bool = True


class TraceEvent(BaseModel):
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    kind: str
    detail: dict[str, Any]


class TaskView(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    idempotency_key: str
    status: TaskStatus = TaskStatus.RECEIVED
    incident: IncidentInput
    plan: IncidentPlan | None = None
    evidence: list[ToolEvidence] = Field(default_factory=list)
    proposal: ActionProposal | None = None
    result: dict[str, Any] | None = None
    trace: list[TraceEvent] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=2)
