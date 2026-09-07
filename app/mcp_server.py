from __future__ import annotations

from pydantic import BaseModel

from mcp.server import MCPServer
from app.tools import ManufacturingTools


class LineMetricsOutput(BaseModel):
    line_id: str
    units_per_hour: int
    baseline_units_per_hour: int
    downtime_events_today: int
    temperature_c: float


class RecentIncidentsOutput(BaseModel):
    line_id: str
    matches: list[dict[str, str]]


mcp = MCPServer("ChampionAI Manufacturing Tools")
tools = ManufacturingTools()


@mcp.tool(structured_output=True)
async def get_line_metrics(line_id: str) -> LineMetricsOutput:
    """Read current production metrics for a manufacturing line."""
    data = await tools.get_line_metrics(line_id)
    return LineMetricsOutput.model_validate(data)


@mcp.tool(structured_output=True)
async def get_recent_incidents(line_id: str) -> RecentIncidentsOutput:
    """Retrieve recent similar incidents and historical resolutions."""
    data = await tools.get_recent_incidents(line_id)
    return RecentIncidentsOutput.model_validate(data)