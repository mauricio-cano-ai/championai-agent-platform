from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(StrEnum):
    INVESTIGATING = "INVESTIGATING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class IncidentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    asset_id: str = Field(min_length=1, max_length=128)
    summary: str = Field(min_length=5, max_length=2000)

    @field_validator("summary")
    @classmethod
    def summary_must_have_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary must contain non-whitespace content")
        return value


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)


class ActionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=1000)
    risk: str = Field(pattern=r"^(low|medium|high)$")


def _new_evidence_list() -> list[Evidence]:
    return []


class TaskRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    request: IncidentRequest
    status: TaskStatus
    plan: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=_new_evidence_list)
    proposal: ActionProposal | None = None
    execution: dict[str, Any] | None = None
    decision_by: str | None = None
    decision_reason: str | None = None
