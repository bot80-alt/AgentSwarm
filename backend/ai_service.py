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


async def execute_agent_task(
    prompt: str,
    success_criteria: str,
    *,
    agent_name: str | None = None,
    agent_description: str | None = None,
) -> tuple[str, bool]:
    """Run an agent task. Returns (output_text, used_mock)."""
    client = _get_client()
    if client is None:
        output = await _mock_execute_agent_task(prompt, success_criteria, agent_name=agent_name)
        return output, True

    persona = "You are a helpful AI marketplace agent."
    if agent_name:
        persona = f"You are {agent_name}."
        if agent_description:
            persona += f" {agent_description}"

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{persona} Complete the user's task clearly "
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
        return content, False
    except (OpenAIError, APIError, ValueError):
        output = await _mock_execute_agent_task(prompt, success_criteria, agent_name=agent_name)
        return output, True


async def _mock_execute_agent_task(
    prompt: str,
    success_criteria: str,
    *,
    agent_name: str | None = None,
) -> str:
    await asyncio.sleep(1.0)
    label = agent_name or "Mock agent"
    return (
        f"{label} response:\n"
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


async def _mock_evaluate_competition(
    prompt: str,
    success_criteria: str,
    submissions: list[dict[str, Any]],
) -> dict[str, Any]:
    await asyncio.sleep(1.0)
    criteria_terms = {
        word.strip(".,!?").lower()
        for word in success_criteria.split()
        if len(word.strip(".,!?")) > 4
    }
    scores: dict[int, float] = {}
    for item in submissions:
        agent_id = int(item["agent_id"])
        output = str(item["output_text"])
        output_lower = output.lower()
        matched = sum(1 for term in criteria_terms if term in output_lower)
        length_bonus = min(len(output.strip()) / 200.0, 1.0)
        scores[agent_id] = matched * 10.0 + length_bonus * 5.0 + len(output.split()) * 0.1

    winner_agent_id = max(scores, key=scores.get)
    reasoning = (
        f"Mock competition judge selected agent {winner_agent_id} with score "
        f"{scores[winner_agent_id]:.1f} based on criteria keyword overlap and output depth."
    )
    return {
        "winner_agent_id": winner_agent_id,
        "scores": scores,
        "reasoning": reasoning,
    }


async def evaluate_competition_submissions(
    prompt: str,
    success_criteria: str,
    submissions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Pick a winning agent from competing submissions."""
    if not submissions:
        raise ValueError("No submissions to evaluate.")

    client = _get_client()
    if client is None:
        return await _mock_evaluate_competition(prompt, success_criteria, submissions)

    entries = []
    for item in submissions:
        entries.append(
            {
                "agent_id": item["agent_id"],
                "agent_name": item.get("agent_name", f"Agent {item['agent_id']}"),
                "output_text": item["output_text"],
            }
        )

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an independent judge for a multi-agent developer competition. "
                        "Return valid JSON with keys: winner_agent_id (integer), scores "
                        "(object mapping agent_id string to float 0-100), reasoning (string)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task prompt:\n{prompt}\n\n"
                        f"Success criteria:\n{success_criteria}\n\n"
                        f"Submissions:\n{json.dumps(entries, indent=2)}\n\n"
                        "Pick the single best submission and score each entrant."
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty evaluation.")
        parsed = json.loads(content)
        winner_agent_id = int(parsed["winner_agent_id"])
        raw_scores = parsed.get("scores", {})
        scores = {int(key): float(value) for key, value in raw_scores.items()}
        reasoning = str(parsed["reasoning"]).strip()
        if winner_agent_id not in {int(item["agent_id"]) for item in submissions}:
            raise ValueError("Winner agent_id is not among submissions.")
        return {
            "winner_agent_id": winner_agent_id,
            "scores": scores,
            "reasoning": reasoning,
        }
    except (OpenAIError, APIError, ValueError, KeyError, json.JSONDecodeError, TypeError):
        return await _mock_evaluate_competition(prompt, success_criteria, submissions)
