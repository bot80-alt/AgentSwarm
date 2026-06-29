"""MCP tool registry and OpenAI function-calling adapters."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from swarm.mcp.cspr_client import AGENT_CASPER_TOOL_WHITELIST, get_cspr_client
from swarm.mcp.filesystem import FilesystemTools
from swarm.mcp.workspace import WorkspaceSandbox, resolve_workspace_root

FILESYSTEM_GROUP = "filesystem"
CSPR_GROUP = "casper"
FILESYSTEM_TOOL_NAMES = ("read_file", "list_directory", "search_files", "file_info")


@dataclass(frozen=True)
class MCPToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str] | None = None
    remote: bool = False


def resolve_enabled_tools(node_tools: list[str]) -> set[str]:
    """Expand tool groups (filesystem, casper) into concrete MCP tool names."""
    enabled: set[str] = set()
    for item in node_tools:
        key = item.strip().lower()
        if not key:
            continue
        if key == FILESYSTEM_GROUP:
            enabled.update(FILESYSTEM_TOOL_NAMES)
        elif key == CSPR_GROUP:
            enabled.update(AGENT_CASPER_TOOL_WHITELIST)
        elif key in FILESYSTEM_TOOL_NAMES:
            enabled.add(key)
        elif key in {name.lower() for name in AGENT_CASPER_TOOL_WHITELIST}:
            for name in AGENT_CASPER_TOOL_WHITELIST:
                if name.lower() == key:
                    enabled.add(name)
                    break
        elif key in AGENT_CASPER_TOOL_WHITELIST:
            enabled.add(key)
    return enabled


class MCPToolRegistry:
    """Registry of local filesystem MCP tools available to swarm agents."""

    def __init__(self, sandbox: WorkspaceSandbox) -> None:
        self.sandbox = sandbox
        self._filesystem = FilesystemTools(sandbox)
        self._specs = self._build_specs()

    @classmethod
    def from_workspace(cls, workspace: str | None = None) -> MCPToolRegistry:
        root = resolve_workspace_root(workspace)
        return cls(WorkspaceSandbox(root))

    @property
    def workspace_root(self) -> str:
        return str(self.sandbox.root)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "group": FILESYSTEM_GROUP,
            }
            for spec in self._specs.values()
        ]

    def openai_tools(self, enabled: set[str]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
            for name, spec in self._specs.items()
            if name in enabled
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        spec = self._specs.get(name)
        if spec is None or spec.handler is None:
            return json.dumps({"error": f"Unknown local tool: {name}"})
        try:
            return spec.handler(**arguments)
        except Exception as exc:  # noqa: BLE001 — tool errors are returned to the model
            return json.dumps({"error": str(exc)})

    def _build_specs(self) -> dict[str, MCPToolSpec]:
        fs = self._filesystem
        return {
            "read_file": MCPToolSpec(
                name="read_file",
                description="Read a text file from the user's local workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path inside the workspace.",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "0-based line offset for pagination.",
                            "default": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of lines to return.",
                            "default": 200,
                        },
                    },
                    "required": ["path"],
                },
                handler=fs.read_file,
            ),
            "list_directory": MCPToolSpec(
                name="list_directory",
                description="List files and folders in a workspace directory.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative directory path (default: workspace root).",
                            "default": ".",
                        },
                    },
                },
                handler=fs.list_directory,
            ),
            "search_files": MCPToolSpec(
                name="search_files",
                description="Find files by glob pattern within the workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern, e.g. '*.md' or '**/*.py'.",
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory to search from (default: workspace root).",
                            "default": ".",
                        },
                    },
                    "required": ["pattern"],
                },
                handler=fs.search_files,
            ),
            "file_info": MCPToolSpec(
                name="file_info",
                description="Get metadata for a file or directory in the workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path inside the workspace.",
                        },
                    },
                    "required": ["path"],
                },
                handler=fs.file_info,
            ),
        }


class CompositeMCPToolRegistry:
    """Filesystem (local) + Casper (remote CSPR.cloud) tool registry."""

    def __init__(
        self,
        local: MCPToolRegistry,
        *,
        casper_specs: dict[str, MCPToolSpec] | None = None,
    ) -> None:
        self._local = local
        self._casper_specs = casper_specs or _default_casper_specs()
        self._client = get_cspr_client()

    @classmethod
    def from_workspace(cls, workspace: str | None = None) -> CompositeMCPToolRegistry:
        return cls(MCPToolRegistry.from_workspace(workspace))

    @property
    def workspace_root(self) -> str:
        return self._local.workspace_root

    def list_tools(self) -> list[dict[str, str]]:
        tools = self._local.list_tools()
        for spec in self._casper_specs.values():
            tools.append(
                {
                    "name": spec.name,
                    "description": spec.description,
                    "group": CSPR_GROUP,
                }
            )
        return tools

    def openai_tools(self, enabled: set[str]) -> list[dict[str, Any]]:
        tools = self._local.openai_tools(enabled)
        for name, spec in self._casper_specs.items():
            if name in enabled:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": spec.name,
                            "description": spec.description,
                            "parameters": spec.parameters,
                        },
                    }
                )
        return tools

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        if name in self._local._specs:  # noqa: SLF001
            return await self._local.execute(name, arguments)
        if name in self._casper_specs:
            if not self._client.enabled or not self._client.api_key:
                return json.dumps(
                    {
                        "error": "CSPR MCP is not configured. Set CSPR_CLOUD_API_KEY.",
                        "tool": name,
                    }
                )
            try:
                return await self._client.call_tool(name, arguments)
            except Exception as exc:  # noqa: BLE001
                return json.dumps({"error": str(exc), "tool": name})
        return json.dumps({"error": f"Unknown tool: {name}"})

    async def hydrate_casper_tools(self) -> None:
        """Refresh remote tool schemas from CSPR MCP when available."""
        if not self._client.enabled or not self._client.api_key:
            return
        try:
            remote_tools = await self._client.list_agent_tools()
            for tool in remote_tools:
                name = tool["name"]
                if name in AGENT_CASPER_TOOL_WHITELIST:
                    self._casper_specs[name] = MCPToolSpec(
                        name=name,
                        description=tool["description"] or f"Casper network tool: {name}",
                        parameters=tool.get("parameters")
                        or {"type": "object", "properties": {}},
                        remote=True,
                    )
        except Exception:
            pass


def _default_casper_specs() -> dict[str, MCPToolSpec]:
    specs: dict[str, MCPToolSpec] = {}
    for name in AGENT_CASPER_TOOL_WHITELIST:
        specs[name] = MCPToolSpec(
            name=name,
            description=f"Casper network tool: {name}",
            parameters={"type": "object", "properties": {}},
            remote=True,
        )
    return specs


def registry_for_tools(
    workspace: str | None,
    enabled_tools: set[str],
) -> MCPToolRegistry | CompositeMCPToolRegistry:
    casper_enabled = bool(enabled_tools & AGENT_CASPER_TOOL_WHITELIST)
    if casper_enabled:
        return CompositeMCPToolRegistry.from_workspace(workspace)
    return MCPToolRegistry.from_workspace(workspace)
