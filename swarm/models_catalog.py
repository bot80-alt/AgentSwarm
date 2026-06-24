"""Supported LLM models for per-node sampling."""

from __future__ import annotations

import os

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

AVAILABLE_MODELS: list[dict[str, str]] = [
    {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "provider": "openai"},
    {"id": "gpt-4o", "label": "GPT-4o", "provider": "openai"},
    {"id": "gpt-4.1-mini", "label": "GPT-4.1 Mini", "provider": "openai"},
    {"id": "gpt-4.1", "label": "GPT-4.1", "provider": "openai"},
    {"id": "o3-mini", "label": "o3-mini", "provider": "openai"},
]
