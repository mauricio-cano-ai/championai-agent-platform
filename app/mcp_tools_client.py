from __future__ import annotations

import asyncio
import shutil

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.reliability import retry_async


class MCPManufacturingClient:
    def __init__(self) -> None:
        self.uv_path = shutil.which("uv")

        if not self.uv_path:
            raise RuntimeError("uv was not found in PATH")

    async def fetch_evidence(
        self,
        line_id: str,
    ) -> tuple[dict, dict]:
        server = StdioServerParameters(
            command=self.uv_path,
            args=[
                "run",
                "--with",
                "mcp==2.2.0",
                "mcp",
                "run",
                "app/mcp_server.py",
            ],
        )

        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                async def call_tool(tool_name: str) -> dict:
                    result = await session.call_tool(
                        tool_name,
                        arguments={"line_id": line_id},
                    )

                    if result.is_error:
                        message = " | ".join(
                            getattr(item, "text", str(item))
                            for item in result.content
                        )
                        raise ConnectionError(
                            f"MCP tool {tool_name} failed: {message}"
                        )

                    if result.structured_content is None:
                        raise ValueError(
                            f"MCP tool {tool_name} returned no structured content"
                        )

                    return result.structured_content

                metric_data, history_data = await asyncio.gather(
                    retry_async(
                        lambda: call_tool("get_line_metrics")
                    ),
                    retry_async(
                        lambda: call_tool("get_recent_incidents")
                    ),
                )

                return metric_data, history_data
