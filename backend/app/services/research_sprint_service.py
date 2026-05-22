"""ResearchSprintService — Intelligent Research Orchestration.

Given a research question and constraints (time, depth, focus), plans
and describes the optimal sequence of tool calls to maximize insight.
Acts as a "research project manager" that knows all available tools
and can compose them into effective workflows.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SPRINT_PLAN_SYSTEM = """You are a research sprint planner with access to a powerful research intelligence platform. Given a question and constraints, plan the optimal sequence of research actions.

Available tool categories:
- DISCOVERY: search_papers, find_papers_openalex, search_vectors (find relevant work)
- EXTRACTION: extract_claims, summarize_paper (pull structured info from papers)
- VERIFICATION: lab_compile, lab_build, lab_start, lab_collect (experimental verification)
- SYNTHESIS: synthesis_convergence, synthesis_contradictions, synthesis_hypotheses (cross-source)
- ADVERSARIAL: red_team_steelman, red_team_premortem, red_team_stress_test (attack claims)
- TEMPORAL: temporal_velocity, temporal_paradigm_shift, temporal_emergence (track evolution)
- STRATEGY: strategy_next_action, strategy_bias, strategy_portfolio (meta-optimization)
- DEBATE: debate_run, debate_quick (multi-perspective argumentation)
- ANALOGY: analogy_find, analogy_transfer (cross-domain reasoning)
- COUNTERFACTUAL: counterfactual_negate, counterfactual_fragility, counterfactual_what_if (what-if)
- PEER_REVIEW: peer_review_simulate (academic review simulation)
- SERENDIPITY: serendipity_bisociate, serendipity_random_walk, serendipity_force_connection (creative)
- BLIND_SPOTS: blind_spot_detect, blind_spot_assumptions, blind_spot_overconfidence (epistemic humility)
- COMPILER: compile_research_brief, compile_research_proposal, compile_gap_analysis (output)

Output JSON with: sprint_plan.goal, sprint_plan.estimated_duration_minutes, sprint_plan.phases (list of phase_name/tools_to_use/rationale/expected_output/dependencies), sprint_plan.critical_path (minimum viable sequence), sprint_plan.parallel_opportunities (what can run simultaneously), sprint_plan.decision_points (where human judgment is needed), sprint_plan.success_criteria (how to know we're done), sprint_plan.risk_mitigation (what to do if tools return empty)."""

SPRINT_PLAN_PROMPT = """Plan a research sprint:

Question: {question}
Domain: {domain}
Depth: {depth} (quick_scan|standard|deep_dive|exhaustive)
Focus: {focus}
Time budget: {time_budget}

Current state:
{state_text}

Plan the optimal tool sequence. Return ONLY valid JSON."""

SPRINT_ADAPT_SYSTEM = """You are a research sprint adapter. Given intermediate results from a research sprint, decide what to do next. Should we go deeper on a finding? Pivot to a new angle? Declare victory? Cut losses?

Output JSON with: adaptation.current_state (brief assessment), adaptation.progress (0-1), adaptation.next_action (tool to call next), adaptation.next_args (arguments for that tool), adaptation.rationale (why this is the best next step), adaptation.pivot_needed (true/false), adaptation.pivot_reason (if pivoting), adaptation.stop_conditions_met (true/false), adaptation.confidence_in_direction (0-1)."""

SPRINT_ADAPT_PROMPT = """Sprint state:

Original question: {question}
Phase: {phase}
Results so far:
{results_text}

Remaining budget: {remaining}

What should we do next? Return ONLY valid JSON."""


class ResearchSprintService:
    """Intelligent research orchestration and sprint planning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan_sprint(
        self,
        question: str,
        *,
        domain: str = "",
        depth: str = "standard",
        focus: str = "",
        time_budget: str = "30 minutes",
        dossier_id: str | None = None,
    ) -> dict:
        """Plan an optimal research sprint."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        state = await self._get_current_state(question, dossier_id)
        state_text = "\n".join(f"- {s}" for s in state[:8]) or "Starting fresh"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPRINT_PLAN_PROMPT.format(
                question=question,
                domain=domain or "general research",
                depth=depth,
                focus=focus or "comprehensive understanding",
                time_budget=time_budget,
                state_text=state_text,
            ),
            system=SPRINT_PLAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        plan = data.get("sprint_plan", data)

        return {
            "question": question,
            "goal": plan.get("goal", question),
            "estimated_minutes": plan.get("estimated_duration_minutes", 30),
            "phases": plan.get("phases", []),
            "critical_path": plan.get("critical_path", []),
            "parallel_opportunities": plan.get("parallel_opportunities", []),
            "decision_points": plan.get("decision_points", []),
            "success_criteria": plan.get("success_criteria", []),
            "risk_mitigation": plan.get("risk_mitigation", []),
        }

    async def adapt_sprint(
        self,
        question: str,
        phase: str,
        results_so_far: list[dict],
        *,
        remaining_budget: str = "15 minutes",
    ) -> dict:
        """Adapt sprint based on intermediate results."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        results_text = "\n".join(
            f"- [{r.get('tool','?')}] {r.get('summary', str(r.get('result','')))[:100]}"
            for r in results_so_far[:8]
        ) or "No results yet"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPRINT_ADAPT_PROMPT.format(
                question=question,
                phase=phase,
                results_text=results_text,
                remaining=remaining_budget,
            ),
            system=SPRINT_ADAPT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        adaptation = data.get("adaptation", data)

        return {
            "progress": adaptation.get("progress", 0),
            "next_action": adaptation.get("next_action", ""),
            "next_args": adaptation.get("next_args", {}),
            "rationale": adaptation.get("rationale", ""),
            "pivot_needed": adaptation.get("pivot_needed", False),
            "pivot_reason": adaptation.get("pivot_reason", ""),
            "stop": adaptation.get("stop_conditions_met", False),
            "confidence": adaptation.get("confidence_in_direction", 0),
        }

    # --- Private helpers ---

    async def _get_current_state(self, question: str, dossier_id: str | None) -> list[str]:
        state = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier:
                    state.append(f"Dossier: {dossier.topic}")
                    state.append(f"Papers seen: {dossier.papers_seen or 0}")
                    state.append(f"Claims: {len(dossier.claims or [])}")
                    state.append(f"Coverage: {dossier.coverage_score or 0}")
                    if dossier.gaps:
                        state.append(f"Gaps: {len(dossier.gaps)}")
            except Exception:
                pass
        if not state:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=question[:100], top_k=3)
                if results:
                    state.append(f"Vector store has {len(results)} relevant items")
                else:
                    state.append("No prior research found")
            except Exception:
                state.append("Starting from scratch")
        return state
