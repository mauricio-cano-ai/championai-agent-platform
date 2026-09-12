"""Protocol-level smoke tests for ChampionAI MCP v2."""

from __future__ import annotations

import inspect

import pytest
from mcp import Client
from mcp.server import MCPServer

import app.mcp_server as mcp_server_module


def _registered_server() -> MCPServer:
    servers = [
        value
        for _, value in inspect.getmembers(mcp_server_module)
        if isinstance(value, MCPServer)
    ]

    assert servers, "app.mcp_server must export an MCPServer instance"
    assert len(servers) == 1, "Expected one canonical MCP server"

    return servers[0]


@pytest.mark.asyncio
async def test_mcp_server_discovers_typed_tools() -> None:
    server = _registered_server()

    async with Client(server) as client:
        result = await client.list_tools()

    assert result.tools

    for tool in result.tools:
        assert tool.name
        assert tool.description
        assert tool.input_schema["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_tool_names_are_unique() -> None:
    server = _registered_server()

    async with Client(server) as client:
        result = await client.list_tools()

    names = [tool.name for tool in result.tools]

    assert len(names) == len(set(names))
