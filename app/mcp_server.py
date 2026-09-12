"""MCP v2 read-only evidence gateway for ChampionAI.

The MCP boundary exposes evidence to agents. It deliberately does not own
approval, authorization, idempotency, execution claims, or mutating side
effects. Those remain deterministic application invariants.
"""

from mcp.server import MCPServer

mcp = MCPServer("ChampionAI Evidence Gateway")


@mcp.tool()
def get_incident_context(incident_id: str) -> dict[str, str]:
    """Return deterministic read-only context for a manufacturing incident."""
    return {
        "incident_id": incident_id,
        "source": "championai-lab",
        "access": "read-only",
    }


@mcp.tool()
def get_asset_context(asset_id: str) -> dict[str, str]:
    """Return deterministic read-only context for an affected asset."""
    return {
        "asset_id": asset_id,
        "source": "championai-lab",
        "access": "read-only",
    }


@mcp.tool()
def get_safety_constraints(asset_id: str) -> dict[str, object]:
    """Return safety constraints that must remain outside model authority."""
    return {
        "asset_id": asset_id,
        "requires_human_approval": True,
        "mutation_allowed": False,
        "authority_boundary": "deterministic-application-layer",
    }


if __name__ == "__main__":
    mcp.run()
