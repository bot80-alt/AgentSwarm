import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import APIError, AsyncOpenAI, OpenAIError


load_dotenv()

PLACEHOLDER_KEYS = {"", "your_openai_api_key_here", "sk-placeholder"}


def _get_client() -> AsyncOpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key in PLACEHOLDER_KEYS:
        return None
    return AsyncOpenAI(api_key=api_key)


async def _mock_execute_agent_task(prompt: str, success_criteria: str) -> str:
    await asyncio.sleep(1.0)
    return (
        "Mock agent response:\n"
        f"Task prompt: {prompt}\n"
        f"Target criteria: {success_criteria}\n"
        "Proposed outcome: This demo agent completed the request with a concise, "
        "structured answer aligned to the stated requirements."
    )


async def _mock_evaluate_task(
    prompt: str,
    success_criteria: str,
    output_text: str,
) -> dict[str, Any]:
    await asyncio.sleep(1.0)
    criteria_terms = {
        word.strip(".,!?").lower()
        for word in success_criteria.split()
        if len(word.strip(".,!?")) > 4
    }
    output_lower = output_text.lower()
    matched = sorted(term for term in criteria_terms if term in output_lower)
    passed = bool(output_text.strip()) and (
        len(matched) >= min(2, len(criteria_terms)) or len(output_text.strip()) > 80
    )
    reasoning = (
        "Mock judge approved the result because the output was non-empty and matched "
        f"these criteria signals: {', '.join(matched) if matched else 'no direct keyword matches, but the answer was sufficiently detailed'}."
        if passed
        else "Mock judge rejected the result because the output was too weak relative to the requested success criteria."
    )
    return {"passed": passed, "reasoning": reasoning}


async def execute_agent_task(prompt: str, success_criteria: str) -> str:
    client = _get_client()
    if client is None:
        return await _mock_execute_agent_task(prompt, success_criteria)

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI marketplace agent. Complete the user's task clearly "
                        "and aim to satisfy the provided success criteria."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Prompt:\n{prompt}\n\n"
                        f"Success criteria:\n{success_criteria}\n\n"
                        "Provide only the agent's final output."
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty completion.")
        return content
    except (OpenAIError, APIError, ValueError):
        return await _mock_execute_agent_task(prompt, success_criteria)


async def evaluate_task(
    prompt: str,
    success_criteria: str,
    output_text: str,
) -> dict[str, Any]:
    client = _get_client()
    if client is None:
        return await _mock_evaluate_task(prompt, success_criteria, output_text)

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an independent evaluator for a pay-for-success AI marketplace. "
                        "Return valid JSON with keys: passed (boolean) and reasoning (string)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original prompt:\n{prompt}\n\n"
                        f"Success criteria:\n{success_criteria}\n\n"
                        f"Agent output:\n{output_text}\n\n"
                        "Evaluate whether the output satisfies the criteria. "
                        "Respond only with JSON."
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty evaluation.")
        parsed = json.loads(content)
        passed = bool(parsed["passed"])
        reasoning = str(parsed["reasoning"]).strip()
        if not reasoning:
            raise ValueError("Judge reasoning was empty.")
        return {"passed": passed, "reasoning": reasoning}
    except (OpenAIError, APIError, ValueError, KeyError, json.JSONDecodeError, TypeError):
        return await _mock_evaluate_task(prompt, success_criteria, output_text)
