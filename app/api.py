from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from .agents import DemoExecutor, DemoInvestigator, DemoPlanner
from .domain import IncidentRequest, TaskRecord
from .orchestrator import InvalidTransitionError, Orchestrator, TaskNotFoundError
from .store import InMemoryTaskStore


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str = Field(min_length=3, max_length=200)


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    runtime = orchestrator or Orchestrator(
        store=InMemoryTaskStore(),
        planner=DemoPlanner(),
        investigator=DemoInvestigator(),
        executor=DemoExecutor(),
    )
    app = FastAPI(
        title="ChampionAI Agent Platform",
        version="1.0.0",
        description=(
            "Deterministic reference implementation of an agent workflow "
            "with explicit human approval before side effects."
        ),
    )

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.post(
        "/v1/incidents",
        response_model=TaskRecord,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["tasks"],
    )
    async def submit(request: IncidentRequest) -> TaskRecord:
        return await runtime.submit(request)

    @app.post("/v1/tasks/{task_id}/approve", response_model=TaskRecord, tags=["tasks"])
    async def approve(task_id: str, decision: DecisionRequest) -> TaskRecord:
        try:
            return await runtime.approve(task_id, approved_by=decision.actor)
        except TaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail="task_not_found") from exc
        except InvalidTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return app


app = create_app()
