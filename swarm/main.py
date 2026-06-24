"""
Runnable 4-node marketing pipeline demonstrating parallel DAG execution.

Run from repo root:
    python -m swarm.main
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swarm.engine import WorkflowEngine
from swarm.workflows import MARKETING_LAUNCH_TEMPLATE_ID, resolve_template


async def main() -> None:
    graph, context = resolve_template(
        MARKETING_LAUNCH_TEMPLATE_ID,
        product="EcoBlend Smart Water Bottle",
        target_audience="health-conscious urban professionals aged 25-40",
        brand_voice="optimistic, science-backed, eco-conscious",
    )
    engine = WorkflowEngine()
    result = await engine.run(graph, global_context=context)

    copy = result.outputs_by_key.get("marketing_copy")
    print("\n" + "=" * 72)
    print("FINAL MARKETING COPY")
    print("=" * 72)
    if copy:
        print(copy.content)
    else:
        print("No marketing copy produced.")

    print("\n--- All node outputs (by key) ---")
    for key, node_result in result.outputs_by_key.items():
        preview = node_result.content.replace("\n", " ")[:120]
        print(f"  {key}: {preview}...")


if __name__ == "__main__":
    asyncio.run(main())
