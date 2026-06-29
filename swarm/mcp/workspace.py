"""Sandboxed workspace root for MCP filesystem access."""

from __future__ import annotations

import os
from pathlib import Path

BLOCKED_EXTENSIONS = {
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".kdbx",
}

MAX_READ_BYTES = 256_000


class WorkspaceError(ValueError):
    """Raised when a filesystem operation violates workspace policy."""


def resolve_workspace_root(override: str | None = None) -> Path:
    """Resolve the MCP workspace directory from override or environment."""
    raw = (override or os.getenv("MCP_WORKSPACE_ROOT", "")).strip()
    if not raw:
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root.resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        path = (repo_root / path).resolve()
    else:
        path = path.resolve()
    if not path.exists():
        raise WorkspaceError(f"MCP workspace does not exist: {path}")
    if not path.is_dir():
        raise WorkspaceError(f"MCP workspace is not a directory: {path}")
    return path


class WorkspaceSandbox:
    """Restrict filesystem operations to a single workspace root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve_path(self, relative_path: str) -> Path:
        cleaned = relative_path.strip().replace("\\", "/").lstrip("/")
        if not cleaned or cleaned in {".", "./"}:
            target = self.root
        else:
            target = (self.root / cleaned).resolve()

        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(
                f"Path {relative_path!r} escapes the MCP workspace."
            ) from exc

        if target.is_symlink():
            real = target.resolve(strict=False)
            try:
                real.relative_to(self.root)
            except ValueError as exc:
                raise WorkspaceError(
                    f"Symlink {relative_path!r} points outside the workspace."
                ) from exc
            target = real

        if target.is_file() and target.suffix.lower() in BLOCKED_EXTENSIONS:
            raise WorkspaceError(
                f"Reading {target.name!r} is blocked for security reasons."
            )
        return target

    def relative_display(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix() or "."
        except ValueError:
            return path.as_posix()
