"""FastAPI-facing adapter for CSPR.cloud MCP."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from swarm.mcp.cspr_client import AGENT_CASPER_TOOL_WHITELIST, CasperMCPClient, get_cspr_client


def get_cspr_status() -> dict[str, Any]:
    """Synchronous wrapper for health check (runs async client in event loop)."""
    client = get_cspr_client()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(client.health_check())

    if loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, client.health_check())
            return future.result(timeout=60)
    return asyncio.run(client.health_check())


async def get_cspr_status_async() -> dict[str, Any]:
    client = get_cspr_client()
    return await client.health_check()


async def verify_account_balance(account_hash: str) -> str:
    client = get_cspr_client()
    snapshot = await client.verify_account_balance(account_hash)
    return json.dumps(snapshot)


async def list_agent_casper_tools() -> list[dict[str, str]]:
    client = get_cspr_client()
    if not client.enabled or not client.api_key:
        return [
            {
                "name": name,
                "description": f"Casper network tool: {name}",
                "group": "casper",
            }
            for name in sorted(AGENT_CASPER_TOOL_WHITELIST)
        ]
    try:
        tools = await client.list_agent_tools()
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "group": "casper",
            }
            for tool in tools
        ]
    except Exception:
        return [
            {
                "name": name,
                "description": f"Casper network tool: {name}",
                "group": "casper",
            }
            for name in sorted(AGENT_CASPER_TOOL_WHITELIST)
        ]


def get_agent_casper_tool_names() -> frozenset[str]:
    return AGENT_CASPER_TOOL_WHITELIST
