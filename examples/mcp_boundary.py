"""MCP boundary sketch: keep tool permissions and payload contracts explicit.

The runnable core does not require MCP. Install `.[interop]` to adapt this contract
against a real MCP server/client without coupling orchestration to transport details.
"""
from pydantic import BaseModel, ConfigDict, Field


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(pattern=r"^[a-z0-9_.-]+$")
    asset_id: str
    read_only: bool = True
