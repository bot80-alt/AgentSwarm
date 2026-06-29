"""Standalone MCP filesystem server for external clients (Cursor, Claude Desktop, etc.)."""

from __future__ import annotations

import argparse
import os

from mcp.server.fastmcp import FastMCP

from swarm.mcp.filesystem import FilesystemTools
from swarm.mcp.workspace import WorkspaceSandbox, resolve_workspace_root

mcp = FastMCP("Agent Swarm Filesystem")
_tools: FilesystemTools | None = None


def _get_tools() -> FilesystemTools:
    global _tools
    if _tools is None:
        root = resolve_workspace_root(os.getenv("MCP_WORKSPACE_ROOT"))
        _tools = FilesystemTools(WorkspaceSandbox(root))
    return _tools


@mcp.tool()
def read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    """Read a text file from the user's local workspace."""
    return _get_tools().read_file(path, offset=offset, limit=limit)


@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List files and folders in a workspace directory."""
    return _get_tools().list_directory(path)


@mcp.tool()
def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern inside the workspace."""
    return _get_tools().search_files(pattern, path=path)


@mcp.tool()
def file_info(path: str) -> str:
    """Return metadata for a file or directory in the workspace."""
    return _get_tools().file_info(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Swarm MCP filesystem server")
    parser.add_argument(
        "--workspace",
        help="Workspace root directory (overrides MCP_WORKSPACE_ROOT)",
    )
    args = parser.parse_args()
    if args.workspace:
        os.environ["MCP_WORKSPACE_ROOT"] = args.workspace
    mcp.run()


if __name__ == "__main__":
    main()
