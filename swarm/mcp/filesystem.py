"""Filesystem tool implementations used by swarm agents and the MCP server."""

from __future__ import annotations

import json
from pathlib import Path

from swarm.mcp.workspace import MAX_READ_BYTES, WorkspaceError, WorkspaceSandbox


class FilesystemTools:
    """Read-only filesystem tools scoped to a workspace sandbox."""

    def __init__(self, sandbox: WorkspaceSandbox) -> None:
        self.sandbox = sandbox

    def read_file(self, path: str, offset: int = 0, limit: int = 200) -> str:
        """Read a text file inside the workspace. Use offset/limit for large files."""
        target = self.sandbox.resolve_path(path)
        if not target.exists():
            raise WorkspaceError(f"File not found: {path}")
        if not target.is_file():
            raise WorkspaceError(f"Not a file: {path}")

        size = target.stat().st_size
        if size > MAX_READ_BYTES:
            raise WorkspaceError(
                f"File too large ({size} bytes). Max allowed: {MAX_READ_BYTES}."
            )

        text = target.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        start = max(0, offset)
        end = start + max(1, min(limit, 500))
        snippet = "\n".join(lines[start:end])
        header = (
            f"path: {self.sandbox.relative_display(target)}\n"
            f"lines: {len(lines)} | showing {start + 1}-{min(end, len(lines))}\n\n"
        )
        return header + snippet

    def list_directory(self, path: str = ".") -> str:
        """List files and folders in a workspace directory."""
        target = self.sandbox.resolve_path(path)
        if not target.exists():
            raise WorkspaceError(f"Directory not found: {path}")
        if not target.is_dir():
            raise WorkspaceError(f"Not a directory: {path}")

        entries: list[dict[str, str | int]] = []
        for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            info: dict[str, str | int] = {
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
            }
            if child.is_file():
                info["size"] = child.stat().st_size
            entries.append(info)

        payload = {
            "path": self.sandbox.relative_display(target),
            "entries": entries,
        }
        return json.dumps(payload, indent=2)

    def search_files(self, pattern: str, path: str = ".") -> str:
        """Search for files matching a glob pattern (e.g. '*.md', '**/*.py')."""
        target = self.sandbox.resolve_path(path)
        if not target.exists():
            raise WorkspaceError(f"Directory not found: {path}")
        if not target.is_dir():
            raise WorkspaceError(f"Not a directory: {path}")

        matches: list[str] = []
        for match in sorted(target.glob(pattern)):
            if match.is_file():
                try:
                    match.relative_to(self.sandbox.root)
                except ValueError:
                    continue
                matches.append(self.sandbox.relative_display(match))
            if len(matches) >= 100:
                break

        return json.dumps(
            {
                "pattern": pattern,
                "path": self.sandbox.relative_display(target),
                "matches": matches,
                "truncated": len(matches) >= 100,
            },
            indent=2,
        )

    def file_info(self, path: str) -> str:
        """Return metadata for a file or directory."""
        target = self.sandbox.resolve_path(path)
        if not target.exists():
            raise WorkspaceError(f"Path not found: {path}")

        stat = target.stat()
        info = {
            "path": self.sandbox.relative_display(target),
            "type": "dir" if target.is_dir() else "file",
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
        }
        if target.is_file():
            info["extension"] = target.suffix
        return json.dumps(info, indent=2)
