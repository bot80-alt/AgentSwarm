"""MCP filesystem integration for swarm agents."""

from swarm.mcp.cspr_client import CasperMCPClient, get_cspr_client
from swarm.mcp.filesystem import FilesystemTools
from swarm.mcp.registry import (
    CSPR_GROUP,
    FILESYSTEM_GROUP,
    CompositeMCPToolRegistry,
    MCPToolRegistry,
    registry_for_tools,
    resolve_enabled_tools,
)
from swarm.mcp.workspace import WorkspaceSandbox, resolve_workspace_root

__all__ = [
    "CSPR_GROUP",
    "CasperMCPClient",
    "CompositeMCPToolRegistry",
    "FILESYSTEM_GROUP",
    "FilesystemTools",
    "MCPToolRegistry",
    "WorkspaceSandbox",
    "get_cspr_client",
    "registry_for_tools",
    "resolve_enabled_tools",
    "resolve_workspace_root",
]
