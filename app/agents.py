from __future__ import annotations

from typing import Any

from .domain import ActionProposal, Evidence, IncidentRequest


class DemoPlanner:
    async def plan(self, request: IncidentRequest) -> list[str]:
        return [
            f"inspect telemetry for {request.asset_id}",
            "compare recent changes with normal operating state",
            "prepare a reversible action proposal for human review",
        ]


class DemoInvestigator:
    async def collect(
        self,
        request: IncidentRequest,
        plan: list[str],
    ) -> list[Evidence | dict[str, Any]]:
        _ = plan
        return [
            Evidence(
                source="telemetry",
                summary=f"Anomaly confirmed for {request.asset_id}",
                confidence=0.84,
            ),
            Evidence(
                source="change_log",
                summary="A recent configuration change is temporally correlated",
                confidence=0.71,
            ),
        ]


class DemoExecutor:
    def __init__(self) -> None:
        self._counter = 0

    async def execute(self, proposal: ActionProposal) -> dict[str, Any]:
        self._counter += 1
        return {
            "action_id": f"demo-action-{self._counter}",
            "status": "accepted",
            "action": proposal.action,
        }
