from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.domain import IncidentInput, IncidentPlan


class OpenAIPlannerAgent:
    """LLM planner backed by the OpenAI Responses API + Pydantic Structured Outputs."""

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Put it in .env or the environment."
            )

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.client = AsyncOpenAI()

    async def plan(self, incident: IncidentInput) -> IncidentPlan:
        response = await self.client.responses.parse(
            model=self.model,
            instructions=(
                "You are the planning agent for a manufacturing incident platform. "
                "Return a concise operational plan using exactly these three tool names: "
                "get_line_metrics, get_recent_incidents, create_maintenance_ticket. "
                "The first two steps gather evidence; the final step prepares a maintenance "
                "ticket. The maintenance action must always require human approval. "
                "Do not invent any other tools."
            ),
            input=(
                "Create the investigation plan for this incident:\n"
                f"line_id={incident.line_id}\n"
                f"description={incident.description}\n"
                f"output_drop_pct={incident.output_drop_pct}"
            ),
            text_format=IncidentPlan,
        )

        parsed: IncidentPlan | None = None

        for output in response.output:
            if output.type != "message":
                continue

            for item in output.content:
                if item.type == "output_text" and item.parsed is not None:
                    parsed = item.parsed
                    break

            if parsed is not None:
                break

        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed IncidentPlan.")

        required_tools = {
            "get_line_metrics",
            "get_recent_incidents",
            "create_maintenance_ticket",
        }
        actual_tools = {step.tool for step in parsed.steps}

        if actual_tools != required_tools:
            raise ValueError(
                "Planner returned an invalid tool set. "
                f"Expected {sorted(required_tools)}, got {sorted(actual_tools)}"
            )

        if not parsed.requires_human_approval:
            raise ValueError(
                "Planner attempted to remove the mandatory human approval gate."
            )

        return parsed
