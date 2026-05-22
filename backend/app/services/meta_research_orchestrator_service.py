"""MetaResearchOrchestratorService — Multi-Engine Research Pipeline.

The orchestration layer that chains multiple engines together in intelligent
sequences. Given a complex research question, it plans which engines to invoke,
in what order, and how to feed outputs between them to produce comprehensive
research intelligence that no single engine could achieve alone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ORCHESTRATE_SYSTEM = """You are a research orchestration strategist. Given a complex research question, plan the optimal sequence of analytical engines to invoke. You have access to these engine categories:

DISCOVERY: hypothesis_generate, serendipity_bisociate, analogy_find
ANALYSIS: argument_map, debate, counterfactual, blind_spot_detect
EVALUATION: replication_predict, peer_review, methodology_audit
SYNTHESIS: insight_crystallize, consensus_map, narrative_generate
TEMPORAL: temporal_momentum, temporal_staleness
STRUCTURAL: graph_analyze, epistemic_network, knowledge_graph
PLANNING: scenario_generate, methodology_recommend, sprint_plan

Design a multi-step pipeline where each step's output feeds the next. The goal is comprehensive understanding that no single engine provides.

Output JSON with: pipeline.question, pipeline.strategy (1-2 sentence approach), pipeline.steps (list of step_number/engine/input_description/what_it_adds/feeds_into list of step numbers), pipeline.expected_output (what the full pipeline produces), pipeline.estimated_depth (shallow|moderate|deep|exhaustive), pipeline.key_insight_types (list of what kinds of insights this pipeline will surface)."""

ORCHESTRATE_PROMPT = """Plan a multi-engine research pipeline:

Question: {question}
Domain: {domain}
Depth requested: {depth}
Focus areas: {focus_text}

Design the optimal engine sequence. Return ONLY valid JSON."""

EXECUTIVE_SYSTEM = """You are a research executive summarizer. Given outputs from multiple analytical engines that were run in sequence on the same question, produce an executive-level synthesis that captures the full picture: what we know, how confident we are, what we should do, and what we're still missing.

Output JSON with: executive.question, executive.bottom_line (1-2 sentences - the answer), executive.confidence (0-1), executive.key_findings (list of finding/source_engine/confidence 0-1), executive.surprises (list of what was unexpected), executive.contradictions (list of between/tension/resolution), executive.action_items (list of action/priority critical|high|medium|low/rationale), executive.remaining_unknowns (list), executive.meta_assessment (how good is our analysis itself)."""

EXECUTIVE_PROMPT = """Produce executive synthesis:

Question: {question}

Engine outputs (in pipeline order):
{outputs_text}

Synthesize into executive-level intelligence. Return ONLY valid JSON."""


class MetaResearchOrchestratorService:
    """Orchestrates multi-engine research pipelines."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan_pipeline(
        self,
        question: str,
        *,
        domain: str = "",
        depth: str = "deep",
        focus: list[str] | None = None,
    ) -> dict:
        """Plan a multi-engine research pipeline for a complex question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        focus_text = "\n".join(f"- {f}" for f in (focus or [])) or "Comprehensive analysis"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ORCHESTRATE_PROMPT.format(
                question=question,
                domain=domain or "research",
                depth=depth,
                focus_text=focus_text,
            ),
            system=ORCHESTRATE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        pipeline = data.get("pipeline", data)

        return {
            "question": question,
            "strategy": pipeline.get("strategy", ""),
            "steps": pipeline.get("steps", []),
            "expected_output": pipeline.get("expected_output", ""),
            "estimated_depth": pipeline.get("estimated_depth", depth),
            "key_insight_types": pipeline.get("key_insight_types", []),
        }

    async def executive_synthesis(
        self,
        question: str,
        engine_outputs: list[dict],
    ) -> dict:
        """Produce executive-level synthesis from multiple engine outputs."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        outputs_text = "\n\n".join(
            f"[Step {i+1} - {o.get('engine', 'unknown')}]: {str(o.get('summary', o.get('result', '')))[:250]}"
            for i, o in enumerate(engine_outputs[:8])
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXECUTIVE_PROMPT.format(
                question=question,
                outputs_text=outputs_text,
            ),
            system=EXECUTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        exe = data.get("executive", data)

        return {
            "question": question,
            "bottom_line": exe.get("bottom_line", ""),
            "confidence": exe.get("confidence", 0),
            "key_findings": exe.get("key_findings", []),
            "surprises": exe.get("surprises", []),
            "contradictions": exe.get("contradictions", []),
            "action_items": exe.get("action_items", []),
            "remaining_unknowns": exe.get("remaining_unknowns", []),
            "meta_assessment": exe.get("meta_assessment", ""),
        }
