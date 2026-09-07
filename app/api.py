from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException

from app.config import get_settings
from app.domain import ApprovalRequest, IncidentInput, TaskView
from app.llm_planner import OpenAIPlannerAgent
from app.mcp_tools_client import MCPManufacturingClient
from app.orchestrator import IncidentOrchestrator
from app.postgres_store import PostgresTaskStore
from app.store import InMemoryTaskStore, TaskStore


settings = get_settings()

store: TaskStore = (
    PostgresTaskStore(settings.database_url)
    if settings.database_url
    else InMemoryTaskStore()
)

mcp_client = MCPManufacturingClient()
planner = OpenAIPlannerAgent()

orchestrator = IncidentOrchestrator(
    store,
    mcp_client=mcp_client,
    planner=planner,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if isinstance(store, PostgresTaskStore):
        await store.init()

    yield


app = FastAPI(
    title="ChampionAI Mini",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "evidence_transport": "mcp",
        "planner": "openai_structured_output",
        "model": planner.model,
    }


@app.post(
    "/v1/incidents",
    response_model=TaskView,
)
async def create_incident(
    incident: IncidentInput,
    idempotency_key: str = Header(
        alias="Idempotency-Key"
    ),
) -> TaskView:
    return await orchestrator.submit(
        incident,
        idempotency_key,
    )


@app.get(
    "/v1/tasks/{task_id}",
    response_model=TaskView,
)
async def get_task(
    task_id: str,
) -> TaskView:
    task = await store.get(task_id)

    if not task:
        raise HTTPException(
            404,
            "Task not found",
        )

    return task


@app.post(
    "/v1/tasks/{task_id}/approve",
    response_model=TaskView,
)
async def approve_task(
    task_id: str,
    approval: ApprovalRequest,
) -> TaskView:
    try:
        return await orchestrator.approve(
            task_id,
            approval.approved_by,
        )

    except KeyError:
        raise HTTPException(
            404,
            "Task not found",
        )

    except ValueError as exc:
        raise HTTPException(
            409,
            str(exc),
        )
