"""Remote CSPR.cloud MCP client (Streamable HTTP)."""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

CSPR_API_KEY_HEADER = "X-CSPR-Cloud-Api-Key"
DEFAULT_CSPR_MCP_URL = "https://mcp.testnet.cspr.cloud/mcp"

# Curated read-only tools exposed to swarm agents via the "casper" tool group.
AGENT_CASPER_TOOL_WHITELIST = frozenset(
    {
        "GetAccountBalance",
        "GetAccount",
        "GetDeploy",
        "GetTransfers",
        "GetNetworkStatus",
        "ResolveCsprName",
        "GetFungibleTokenActions",
        "BuildTransferTransaction",
    }
)


def _is_cspr_enabled() -> bool:
    explicit = os.getenv("CSPR_MCP_ENABLED", "").strip().lower()
    if explicit in {"0", "false", "no"}:
        return False
    if explicit in {"1", "true", "yes"}:
        return True
    api_key = os.getenv("CSPR_CLOUD_API_KEY", "").strip()
    return bool(api_key)


def _get_cspr_url() -> str:
    return os.getenv("CSPR_MCP_URL", DEFAULT_CSPR_MCP_URL).strip() or DEFAULT_CSPR_MCP_URL


def _get_api_key() -> str:
    return os.getenv("CSPR_CLOUD_API_KEY", "").strip()


def _tool_result_to_text(result: Any) -> str:
    if result is None:
        return ""
    if hasattr(result, "content"):
        parts: list[str] = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) if parts else json.dumps({"result": str(result)})
    return json.dumps(result, default=str)


class CasperMCPClient:
    """Connects to the hosted CSPR.cloud MCP server over Streamable HTTP."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.url = url or _get_cspr_url()
        self.api_key = api_key if api_key is not None else _get_api_key()
        self.enabled = enabled if enabled is not None else _is_cspr_enabled()
        self._tools_cache: list[dict[str, Any]] | None = None

    @property
    def network(self) -> str:
        if "testnet" in self.url.lower():
            return "testnet"
        return "mainnet"

    @asynccontextmanager
    async def _session(self):
        if not self.enabled or not self.api_key:
            raise RuntimeError("CSPR MCP is not configured (missing API key or disabled).")

        headers = {CSPR_API_KEY_HEADER: self.api_key}
        async with httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30.0, read=120.0),
        ) as http_client:
            async with streamable_http_client(
                url=self.url,
                http_client=http_client,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session

    async def health_check(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "url": self.url,
                "network": self.network,
                "connected": False,
                "tool_count": 0,
                "error": "CSPR MCP is disabled.",
            }
        if not self.api_key:
            return {
                "enabled": False,
                "url": self.url,
                "network": self.network,
                "connected": False,
                "tool_count": 0,
                "error": "CSPR_CLOUD_API_KEY is not set.",
            }
        try:
            tools = await self.list_tools(refresh=True)
            return {
                "enabled": True,
                "url": self.url,
                "network": self.network,
                "connected": True,
                "tool_count": len(tools),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "enabled": True,
                "url": self.url,
                "network": self.network,
                "connected": False,
                "tool_count": 0,
                "error": str(exc),
            }

    async def list_tools(self, *, refresh: bool = False) -> list[dict[str, Any]]:
        if self._tools_cache is not None and not refresh:
            return self._tools_cache

        async with self._session() as session:
            listed = await session.list_tools()
            tools: list[dict[str, Any]] = []
            for tool in listed.tools:
                schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": schema or {"type": "object", "properties": {}},
                    }
                )
            self._tools_cache = tools
            return tools

    async def list_agent_tools(self) -> list[dict[str, Any]]:
        all_tools = await self.list_tools()
        return [tool for tool in all_tools if tool["name"] in AGENT_CASPER_TOOL_WHITELIST]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        async with self._session() as session:
            result = await session.call_tool(name, arguments)
            return _tool_result_to_text(result)

    async def verify_account_balance(self, account_hash: str) -> dict[str, Any]:
        """Fetch account balance via CSPR MCP; returns a JSON-serializable snapshot."""
        tools = await self.list_tools()
        tool_names = {tool["name"] for tool in tools}

        balance_tool = None
        for candidate in ("GetAccountBalance", "GetAccount"):
            if candidate in tool_names:
                balance_tool = candidate
                break

        if balance_tool is None:
            return {
                "verified": False,
                "account_hash": account_hash,
                "error": "No balance tool available on CSPR MCP server.",
            }

        args: dict[str, Any]
        if balance_tool == "GetAccountBalance":
            args = {"accountHash": account_hash}
        else:
            args = {"accountHash": account_hash}

        try:
            raw = await self.call_tool(balance_tool, args)
            return {
                "verified": True,
                "account_hash": account_hash,
                "tool": balance_tool,
                "snapshot": raw,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "verified": False,
                "account_hash": account_hash,
                "tool": balance_tool,
                "error": str(exc),
            }


_default_client: CasperMCPClient | None = None


def get_cspr_client() -> CasperMCPClient:
    global _default_client
    if _default_client is None:
        _default_client = CasperMCPClient()
    return _default_client
