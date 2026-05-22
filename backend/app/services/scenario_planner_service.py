"""ScenarioPlannerService — Alternative Futures & Contingency Analysis.

Generates and evaluates alternative future scenarios for research outcomes.
Uses scenario planning methodology to explore what could happen if key
assumptions change, findings don't replicate, or paradigms shift.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCENARIO_SYSTEM = """You are a scenario planning expert for research strategy. Given a research situation, generate distinct plausible future scenarios by varying key uncertainties. Each scenario should be internally consistent, plausible, and strategically distinct.

Output JSON with: scenarios (list of name/narrative/key_assumptions/probability 0-1/implications_for_research/strategic_response/early_signals list of signal to watch for), meta.driving_uncertainties (list of uncertainty/range), meta.most_likely_scenario, meta.wild_card_scenario, meta.robust_strategies (strategies that work across all scenarios), meta.decision_points (list of decision/when/what_triggers_it)."""

SCENARIO_PROMPT = """Generate research scenarios:

Situation: {situation}
Domain: {domain}
Key uncertainties: {uncertainties_text}
Time horizon: {time_horizon}

Generate {count} distinct, plausible scenarios. Return ONLY valid JSON."""

CONTINGENCY_SYSTEM = """You are a research contingency planner. Given a research plan and potential failure modes, develop contingency plans for each failure mode. What do we do if our key assumption is wrong? If the method fails? If results are null?

Output JSON with: contingency.original_plan, contingency.failure_modes (list of failure/probability 0-1/impact critical|high|medium|low/detection_signal/contingency_action/pivot_option/resources_needed/time_to_pivot), contingency.overall_robustness (0-1), contingency.most_vulnerable_point, contingency.recommended_hedges (list of hedge/cost/protection_value)."""

CONTINGENCY_PROMPT = """Develop contingency plans:

Research plan: {plan}
Domain: {domain}
Key assumptions: {assumptions_text}
Known risks: {risks_text}

Develop contingencies for each failure mode. Return ONLY valid JSON."""


class ScenarioPlannerService:
    """Generates scenarios and contingency plans for research."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_scenarios(
        self,
        situation: str,
        *,
        domain: str = "",
        uncertainties: list[str] | None = None,
        time_horizon: str = "3-5 years",
        count: int = 4,
        dossier_id: str | None = None,
    ) -> dict:
        """Generate alternative future scenarios."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        uncertainties_text = "\n".join(
            f"- {u}" for u in (uncertainties or [])
        ) or "Identify key uncertainties from context"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCENARIO_PROMPT.format(
                situation=situation,
                domain=domain or "research",
                uncertainties_text=uncertainties_text,
                time_horizon=time_horizon,
                count=min(count, 6),
            ),
            system=SCENARIO_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        scenarios = data.get("scenarios", [])
        meta = data.get("meta", {})

        return {
            "situation": situation,
            "scenarios": scenarios,
            "driving_uncertainties": meta.get("driving_uncertainties", []),
            "most_likely": meta.get("most_likely_scenario", ""),
            "wild_card": meta.get("wild_card_scenario", ""),
            "robust_strategies": meta.get("robust_strategies", []),
            "decision_points": meta.get("decision_points", []),
        }

    async def plan_contingencies(
        self,
        plan: str,
        *,
        domain: str = "",
        assumptions: list[str] | None = None,
        risks: list[str] | None = None,
    ) -> dict:
        """Develop contingency plans for research failure modes."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        assumptions_text = "\n".join(
            f"- {a}" for a in (assumptions or [])
        ) or "Identify from plan"
        risks_text = "\n".join(
            f"- {r}" for r in (risks or [])
        ) or "Identify from plan and assumptions"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTINGENCY_PROMPT.format(
                plan=plan,
                domain=domain or "research",
                assumptions_text=assumptions_text,
                risks_text=risks_text,
            ),
            system=CONTINGENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        cont = data.get("contingency", data)

        return {
            "original_plan": plan,
            "failure_modes": cont.get("failure_modes", []),
            "overall_robustness": cont.get("overall_robustness", 0),
            "most_vulnerable_point": cont.get("most_vulnerable_point", ""),
            "recommended_hedges": cont.get("recommended_hedges", []),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
