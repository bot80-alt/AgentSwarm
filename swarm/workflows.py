"""Built-in workflow templates for the swarm framework."""

from __future__ import annotations

from typing import Any

from swarm.graph import Node, WorkflowGraph
from swarm.models_catalog import DEFAULT_MODEL

MARKETING_LAUNCH_TEMPLATE_ID = "marketing_launch"
DEVELOPER_COMPETITION_TEMPLATE_ID = "developer_competition"


def _marketing_node_defs() -> list[dict[str, Any]]:
    return [
        {
            "id": "market_researcher",
            "name": "Market Researcher",
            "persona": (
                "You are a senior market research analyst specializing in consumer "
                "health and sustainability products. Produce concise, data-informed insights."
            ),
            "task": (
                "Research the market opportunity for '{product}' targeting "
                "{target_audience}. Cover market size signals, trends, and buyer motivations."
            ),
            "dependencies": [],
            "input_keys": [],
            "output_key": "market_research",
            "tools": ["filesystem", "web_search", "trend_analysis"],
            "model": DEFAULT_MODEL,
            "execution_mode": "parallel",
        },
        {
            "id": "competitor_analyst",
            "name": "Competitor Analyst",
            "persona": (
                "You are a competitive intelligence specialist. Map competitor positioning, "
                "pricing, and differentiation gaps with actionable clarity."
            ),
            "task": (
                "Analyze top competitors for '{product}'. Identify positioning gaps "
                "and opportunities versus {target_audience} needs."
            ),
            "dependencies": [],
            "input_keys": [],
            "output_key": "competitor_analysis",
            "tools": ["web_search", "comparison_matrix"],
            "model": DEFAULT_MODEL,
            "execution_mode": "parallel",
        },
        {
            "id": "report_synthesizer",
            "name": "Report Synthesizer",
            "persona": (
                "You are a strategy consultant who synthesizes research into executive-ready "
                "briefs. Merge upstream inputs without losing nuance."
            ),
            "task": (
                "Synthesize market research and competitor analysis into a unified launch "
                "strategy brief for '{product}'."
            ),
            "dependencies": ["market_researcher", "competitor_analyst"],
            "input_keys": ["market_research", "competitor_analysis"],
            "output_key": "strategy_brief",
            "tools": ["summarization"],
            "model": DEFAULT_MODEL,
            "execution_mode": "serial",
        },
        {
            "id": "copywriter",
            "name": "Copywriter",
            "persona": (
                "You are an award-winning marketing copywriter. Write compelling, "
                "conversion-focused copy grounded in strategy — never generic fluff."
            ),
            "task": (
                "Using the strategy brief, write final launch marketing copy for '{product}': "
                "headline, subheadline, 3 bullet benefits, and a CTA. Brand voice: {brand_voice}."
            ),
            "dependencies": ["report_synthesizer"],
            "input_keys": ["strategy_brief"],
            "output_key": "marketing_copy",
            "tools": ["brand_voice"],
            "model": DEFAULT_MODEL,
            "execution_mode": "serial",
        },
    ]


def _interpolate(text: str, context: dict[str, str]) -> str:
    try:
        return text.format(**context)
    except KeyError:
        return text


def _build_node(defn: dict[str, Any], context: dict[str, str]) -> Node:
    return Node(
        id=defn["id"],
        name=defn["name"],
        persona=defn["persona"],
        task=_interpolate(defn["task"], context),
        dependencies=defn["dependencies"],
        input_keys=defn["input_keys"],
        output_key=defn["output_key"],
        tools=defn["tools"],
        model=defn.get("model", DEFAULT_MODEL),
        execution_mode=defn.get("execution_mode", "parallel"),
    )


def apply_node_overrides(graph: WorkflowGraph, overrides: list[dict[str, Any]]) -> WorkflowGraph:
    override_map = {item["node_id"]: item for item in overrides}
    updated = WorkflowGraph(name=graph.name)
    for node_id, node in graph.nodes.items():
        patch = override_map.get(node_id, {})
        updated.add_node(
            node.model_copy(
                update={
                    key: patch[key]
                    for key in ("task", "persona", "model", "execution_mode", "tools")
                    if key in patch and patch[key] is not None
                }
            )
        )
    updated.validate()
    return updated


def build_marketing_workflow(
    *,
    product: str,
    target_audience: str,
    brand_voice: str = "optimistic, science-backed, eco-conscious",
    node_overrides: list[dict[str, Any]] | None = None,
) -> WorkflowGraph:
    context = {
        "product": product,
        "target_audience": target_audience,
        "brand_voice": brand_voice,
    }
    graph = WorkflowGraph(name="marketing_launch")
    for defn in _marketing_node_defs():
        graph.add_node(_build_node(defn, context))

    if node_overrides:
        graph = apply_node_overrides(graph, node_overrides)
    graph.validate()
    return graph


def graph_topology(graph: WorkflowGraph) -> dict[str, Any]:
    layers = graph.topological_layers()
    return {
        "name": graph.name,
        "layers": layers,
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "dependencies": node.dependencies,
                "output_key": node.output_key,
                "tools": node.tools,
                "persona": node.persona,
                "task": node.task,
                "model": node.model or DEFAULT_MODEL,
                "execution_mode": node.execution_mode,
            }
            for node in graph.nodes.values()
        ],
        "edges": [
            {"from": dep_id, "to": node.id}
            for node in graph.nodes.values()
            for dep_id in node.dependencies
        ],
    }


def _developer_competition_node_defs() -> list[dict[str, Any]]:
    return [
        {
            "id": "proposal_writer",
            "name": "Proposal Writer",
            "persona": (
                "You are a senior proposal writer. Produce structured, persuasive deliverables "
                "for client RFPs."
            ),
            "task": (
                "Solve the client task for '{product}'. Deliverable must satisfy: "
                "{success_criteria}"
            ),
            "dependencies": [],
            "input_keys": [],
            "output_key": "proposal_writer_output",
            "tools": ["casper"],
            "model": DEFAULT_MODEL,
            "execution_mode": "parallel",
        },
        {
            "id": "support_triage",
            "name": "Support Triage Specialist",
            "persona": (
                "You are a support triage specialist who turns messy requests into clear, "
                "actionable solutions."
            ),
            "task": (
                "Solve the client task for '{product}'. Deliverable must satisfy: "
                "{success_criteria}"
            ),
            "dependencies": [],
            "input_keys": [],
            "output_key": "support_triage_output",
            "tools": ["casper"],
            "model": DEFAULT_MODEL,
            "execution_mode": "parallel",
        },
        {
            "id": "competition_judge",
            "name": "Competition Judge",
            "persona": (
                "You are an impartial judge for a developer agent competition. Compare submissions "
                "and pick the best answer against the success criteria."
            ),
            "task": (
                "Review all competing agent outputs and select the winning submission for "
                "'{product}'. Criteria: {success_criteria}"
            ),
            "dependencies": ["proposal_writer", "support_triage"],
            "input_keys": ["proposal_writer_output", "support_triage_output"],
            "output_key": "competition_winner",
            "tools": [],
            "model": DEFAULT_MODEL,
            "execution_mode": "serial",
        },
    ]


def build_developer_competition_workflow(
    *,
    product: str,
    success_criteria: str,
    node_overrides: list[dict[str, Any]] | None = None,
) -> WorkflowGraph:
    context = {
        "product": product,
        "success_criteria": success_criteria,
        "target_audience": "competition entrants",
        "brand_voice": "professional",
    }
    graph = WorkflowGraph(name="developer_competition")
    for defn in _developer_competition_node_defs():
        graph.add_node(_build_node(defn, context))

    if node_overrides:
        graph = apply_node_overrides(graph, node_overrides)
    graph.validate()
    return graph


def list_templates() -> list[dict[str, Any]]:
    sample = build_marketing_workflow(
        product="Your Product",
        target_audience="your target audience",
    )
    topology = graph_topology(sample)
    competition_sample = build_developer_competition_workflow(
        product="Client RFP task",
        success_criteria="Clear, actionable deliverable with acceptance criteria met",
    )
    competition_topology = graph_topology(competition_sample)
    return [
        {
            "id": MARKETING_LAUNCH_TEMPLATE_ID,
            "name": "Marketing Launch Pipeline",
            "description": (
                "Four-node DAG: parallel market research and competitor analysis, "
                "strategy synthesis, then final copywriting."
            ),
            "default_product": "EcoBlend Smart Water Bottle",
            "default_target_audience": "health-conscious urban professionals aged 25-40",
            "default_brand_voice": "optimistic, science-backed, eco-conscious",
            "final_output_key": "marketing_copy",
            "topology": topology,
        },
        {
            "id": DEVELOPER_COMPETITION_TEMPLATE_ID,
            "name": "Developer Agent Competition",
            "description": (
                "Parallel developer agents compete on the same task; a judge node picks "
                "the winning submission."
            ),
            "default_product": "Build a REST API health-check endpoint",
            "default_target_audience": "competition entrants",
            "default_brand_voice": "professional, precise",
            "final_output_key": "competition_winner",
            "topology": competition_topology,
        },
    ]


def resolve_template(
    template_id: str,
    *,
    product: str,
    target_audience: str,
    brand_voice: str,
    node_overrides: list[dict[str, Any]] | None = None,
) -> tuple[WorkflowGraph, dict[str, Any]]:
    if template_id == MARKETING_LAUNCH_TEMPLATE_ID:
        graph = build_marketing_workflow(
            product=product,
            target_audience=target_audience,
            brand_voice=brand_voice,
            node_overrides=node_overrides,
        )
        context = {
            "product": product,
            "target_audience": target_audience,
            "brand_voice": brand_voice,
        }
        return graph, context
    if template_id == DEVELOPER_COMPETITION_TEMPLATE_ID:
        graph = build_developer_competition_workflow(
            product=product,
            success_criteria=brand_voice,
            node_overrides=node_overrides,
        )
        context = {
            "product": product,
            "target_audience": target_audience,
            "brand_voice": brand_voice,
            "success_criteria": brand_voice,
        }
        return graph, context
    raise ValueError(f"Unknown workflow template: {template_id!r}")
