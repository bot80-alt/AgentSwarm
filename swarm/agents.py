"""Base LLM agent wrapper for swarm nodes."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import APIError, AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field

load_dotenv()

PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "sk-placeholder"}


class AgentContext(BaseModel):
    """Incoming data passed to a node from the orchestration engine."""

    node_id: str
    node_name: str
    persona: str
    task: str
    tools: list[str] = Field(default_factory=list)
    upstream_outputs: dict[str, Any] = Field(default_factory=dict)
    global_context: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None


class NodeResult(BaseModel):
    """Structured output produced by a single node execution."""

    node_id: str
    node_name: str
    output_key: str
    content: str
    structured: dict[str, Any] = Field(default_factory=dict)
    model: str = "mock"
    used_mock: bool = True


def _get_openai_client() -> AsyncOpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key in PLACEHOLDER_KEYS:
        return None
    return AsyncOpenAI(api_key=api_key)


def _format_upstream_context(upstream: dict[str, Any]) -> str:
    if not upstream:
        return "No upstream node outputs yet."
    sections: list[str] = []
    for key, value in upstream.items():
        if isinstance(value, NodeResult):
            sections.append(f"### {value.node_name} [{key}]\n{value.content}")
        elif isinstance(value, dict) and "content" in value:
            sections.append(f"### {key}\n{value['content']}")
        else:
            sections.append(f"### {key}\n{value}")
    return "\n\n".join(sections)


class BaseLLMAgent:
    """Formats node context into a prompt, calls the LLM, and structures output."""

    def __init__(
        self,
        *,
        model: str | None = None,
        temperature: float = 0.4,
        mock_delay_seconds: float = 1.2,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.mock_delay_seconds = mock_delay_seconds
        self._client = _get_openai_client()

    async def run(
        self,
        context: AgentContext,
        *,
        output_key: str,
        model: str | None = None,
    ) -> NodeResult:
        prompt = self._build_prompt(context)
        resolved_model = model or context.model or self.model
        used_mock = self._client is None

        if used_mock:
            content, structured = await self._mock_complete(context, prompt)
            model_name = "mock"
        else:
            content, structured, model_name = await self._llm_complete(
                context,
                prompt,
                model=resolved_model,
            )

        return NodeResult(
            node_id=context.node_id,
            node_name=context.node_name,
            output_key=output_key,
            content=content,
            structured=structured,
            model=model_name,
            used_mock=used_mock,
        )

    def _build_prompt(self, context: AgentContext) -> str:
        upstream_text = _format_upstream_context(context.upstream_outputs)
        global_text = json.dumps(context.global_context, indent=2) if context.global_context else "{}"
        tools_text = ", ".join(context.tools) if context.tools else "none"

        return (
            f"Global context:\n{global_text}\n\n"
            f"Upstream node outputs:\n{upstream_text}\n\n"
            f"Your task:\n{context.task}\n\n"
            f"Available tools: {tools_text}\n\n"
            "Respond with a clear, structured analysis suitable for downstream agents."
        )

    async def _llm_complete(
        self,
        context: AgentContext,
        user_prompt: str,
        *,
        model: str,
    ) -> tuple[str, dict[str, Any], str]:
        assert self._client is not None
        try:
            response = await self._client.chat.completions.create(
                model=model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": context.persona},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise ValueError("LLM returned empty content.")
            structured = {
                "summary": content[:280] + ("..." if len(content) > 280 else ""),
                "word_count": len(content.split()),
            }
            return content, structured, model
        except (OpenAIError, APIError, ValueError):
            content, structured = await self._mock_complete(context, user_prompt)
            return content, structured, "mock-fallback"

    async def _mock_complete(
        self,
        context: AgentContext,
        user_prompt: str,
    ) -> tuple[str, dict[str, Any]]:
        await asyncio.sleep(self.mock_delay_seconds)
        upstream_names = list(context.upstream_outputs.keys())
        upstream_note = (
            f" Incorporated insights from: {', '.join(upstream_names)}."
            if upstream_names
            else " Executed as an independent root node."
        )
        content = (
            f"[{context.node_name}] Mock LLM output for task: {context.task.strip()}"
            f"{upstream_note}\n\n"
            f"Key findings:\n"
            f"- Persona-driven analysis from {context.node_name}.\n"
            f"- Actionable bullet points aligned to the task brief.\n"
            f"- Ready for handoff to downstream nodes."
        )
        structured = {
            "summary": content[:280],
            "word_count": len(content.split()),
            "upstream_sources": upstream_names,
        }
        return content, structured
