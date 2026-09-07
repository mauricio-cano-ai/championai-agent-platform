from __future__ import annotations

import asyncio

from app.domain import ActionProposal, IncidentInput, IncidentPlan, PlanStep, ToolEvidence
from app.mcp_tools_client import MCPManufacturingClient
from app.reliability import retry_async
from app.tools import ManufacturingTools


class PlannerAgent:
    async def plan(self, incident: IncidentInput) -> IncidentPlan:
        """Structured planning output; intentionally deterministic for a repeatable demo."""
        return IncidentPlan(
            objective=f"Diagnose production loss on {incident.line_id} and propose a safe next action",
            steps=[
                PlanStep(
                    id="metrics",
                    agent="investigator",
                    tool="get_line_metrics",
                    purpose="Quantify current production and downtime symptoms",
                ),
                PlanStep(
                    id="history",
                    agent="investigator",
                    tool="get_recent_incidents",
                    purpose="Find similar failures and prior resolutions",
                ),
                PlanStep(
                    id="proposal",
                    agent="executor",
                    tool="create_maintenance_ticket",
                    purpose="Prepare a maintenance action for human approval",
                ),
            ],
            requires_human_approval=True,
        )


class InvestigatorAgent:
    def __init__(
        self,
        tools: ManufacturingTools | None = None,
        mcp_client: MCPManufacturingClient | None = None,
    ) -> None:
        self.tools = tools
        self.mcp_client = mcp_client

        if self.tools is None and self.mcp_client is None:
            raise ValueError(
                "InvestigatorAgent requires tools or an MCP client"
            )

    async def investigate(
        self,
        incident: IncidentInput,
    ) -> list[ToolEvidence]:
        if self.mcp_client is not None:
            metric_data, history_data = await self.mcp_client.fetch_evidence(
                incident.line_id
            )
        else:
            assert self.tools is not None

            async def metrics():
                return await retry_async(
                    lambda: self.tools.get_line_metrics(
                        incident.line_id
                    )
                )

            async def history():
                return await retry_async(
                    lambda: self.tools.get_recent_incidents(
                        incident.line_id
                    )
                )

            metric_data, history_data = await asyncio.gather(
                metrics(),
                history(),
            )

        return [
            ToolEvidence(
                tool="get_line_metrics",
                data=metric_data,
            ),
            ToolEvidence(
                tool="get_recent_incidents",
                data=history_data,
            ),
        ]


class ExecutorAgent:
    async def propose(
        self,
        incident: IncidentInput,
        evidence: list[ToolEvidence],
    ) -> ActionProposal:
        history = next(
            item.data
            for item in evidence
            if item.tool == "get_recent_incidents"
        )

        match = history["matches"][0]

        return ActionProposal(
            action_type="create_maintenance_ticket",
            reason=(
                f"Current symptoms resemble {match['incident_id']} "
                f"({match['root_cause']}); "
                f"recommended check: {match['resolution']}"
            ),
            payload={"line_id": incident.line_id},
            requires_approval=True,
        )
