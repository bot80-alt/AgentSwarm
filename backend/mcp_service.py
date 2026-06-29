from __future__ import annotations

import json
import os
from typing import Any

from cspr_service import list_agent_casper_tools
from swarm.mcp.registry import CSPR_GROUP, FILESYSTEM_GROUP, MCPToolRegistry
from swarm.mcp.workspace import WorkspaceError, resolve_workspace_root


def get_mcp_status(workspace_override: str | None = None) -> dict[str, Any]:
    """Return MCP filesystem + Casper server status for API consumers."""
    enabled = os.getenv("MCP_ENABLED", "true").strip().lower() not in {"0", "false", "no"}
    tool_groups = [FILESYSTEM_GROUP]
    try:
        root = resolve_workspace_root(workspace_override)
        registry = MCPToolRegistry.from_workspace(str(root))
        tools = registry.list_tools()
        cspr_enabled = os.getenv("CSPR_MCP_ENABLED", "").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        if cspr_enabled or os.getenv("CSPR_CLOUD_API_KEY", "").strip():
            tool_groups.append(CSPR_GROUP)
            try:
                import asyncio

                casper_tools = asyncio.run(list_agent_casper_tools())
                tools.extend(casper_tools)
            except Exception:
                pass
        return {
            "enabled": enabled,
            "workspace_root": str(root),
            "tool_groups": tool_groups,
            "tools": tools,
            "error": None,
        }
    except WorkspaceError as exc:
        return {
            "enabled": enabled,
            "workspace_root": workspace_override or os.getenv("MCP_WORKSPACE_ROOT") or None,
            "tool_groups": tool_groups,
            "tools": [],
            "error": str(exc),
        }


def get_mcp_tools() -> list[dict[str, str]]:
    registry = MCPToolRegistry.from_workspace()
    tools = registry.list_tools()
    try:
        import asyncio

        tools.extend(asyncio.run(list_agent_casper_tools()))
    except Exception:
        pass
    return tools


def serialize_tools(tools: list[str]) -> str:
    return json.dumps(tools)


def deserialize_tools(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return []
