from __future__ import annotations

import json
import os

import uvicorn
from starlette.applications import Starlette

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)
from a2a.types.a2a_pb2 import TaskState
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from app.agents import InvestigatorAgent
from app.domain import IncidentInput
from app.mcp_tools_client import MCPManufacturingClient


HOST = "127.0.0.1"
PORT = 9999
PUBLIC_URL = f"http://{HOST}:{PORT}"
AGENT_PATH = "/investigator"


class InvestigatorA2AExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if context.message is None:
            raise ValueError("A2A request contains no message")

        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message(
                "Investigator is collecting evidence via MCP."
            ),
        )

        try:
            raw_request = get_message_text(context.message)

            incident = IncidentInput.model_validate_json(
                raw_request
            )

            investigator = InvestigatorAgent(
                mcp_client=MCPManufacturingClient()
            )

            evidence = await investigator.investigate(
                incident
            )

            response = {
                "agent": "ChampionAI Investigator",
                "line_id": incident.line_id,
                "evidence": [
                    item.model_dump()
                    for item in evidence
                ],
            }

            await updater.add_artifact(
                parts=[
                    new_text_part(
                        text=json.dumps(
                            response,
                            indent=2,
                        ),
                        media_type="application/json",
                    )
                ]
            )

            await updater.update_status(
                state=TaskState.TASK_STATE_COMPLETED,
                message=new_text_message(
                    "Investigation complete."
                ),
            )

        except Exception as exc:
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message(
                    f"{type(exc).__name__}: {exc}"
                ),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError(
            "Cancel is not supported in this demo."
        )


agent_card = AgentCard(
    name="ChampionAI Investigator",
    description=(
        "Remote manufacturing investigation agent that "
        "collects operational evidence through MCP tools."
    ),
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(
        streaming=True
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url=f"{PUBLIC_URL}{AGENT_PATH}",
            protocol_version="1.0",
        )
    ],
    skills=[
        AgentSkill(
            id="investigate-manufacturing-incident",
            name="Investigate manufacturing incident",
            description=(
                "Collect current line metrics and similar "
                "historical incidents."
            ),
            input_modes=["text/plain"],
            output_modes=["application/json"],
            tags=[
                "manufacturing",
                "investigation",
                "mcp",
                "a2a",
            ],
            examples=[
                (
                    '{"line_id":"PACK-03",'
                    '"description":"Packaging line stopped '
                    'twice today.","output_drop_pct":18}'
                )
            ],
        )
    ],
)


def build_app() -> Starlette:
    handler = DefaultRequestHandler(
        agent_executor=InvestigatorA2AExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    routes = []

    routes.extend(
        create_agent_card_routes(
            agent_card,
            card_url=(
                f"{AGENT_PATH}"
                f"{AGENT_CARD_WELL_KNOWN_PATH}"
            ),
        )
    )

    routes.extend(
        create_jsonrpc_routes(
            handler,
            rpc_url=AGENT_PATH,
        )
    )

    return Starlette(routes=routes)


if __name__ == "__main__":
    print(
        "ChampionAI Investigator A2A Agent"
    )
    print(
        f"Agent Card: "
        f"{PUBLIC_URL}{AGENT_PATH}"
        f"{AGENT_CARD_WELL_KNOWN_PATH}"
    )
    print(
        f"JSON-RPC: {PUBLIC_URL}{AGENT_PATH}"
    )

    uvicorn.run(
        build_app(),
        host=HOST,
        port=PORT,
    )
