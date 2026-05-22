"""EpistemicDecisionPrematureClosureService - Premature Closure Detection.

Detects premature closure where decisions are made before adequate exploration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_PREMATURE_CLOSURE_SYSTEM = """You are an epistemic decision premature closure specialist. Given decision timing, assess whether closure occurs before adequate exploration:

Key concepts:
- Premature closure: reaching conclusions before sufficient evidence or exploration
- Need for closure: psychological drive to resolve ambiguity quickly
- Exploration truncation: cutting short the search for alternatives
- Satisficing degradation: accepting first adequate option without comparison

When premature closure IS present:
- Decision made before adequate exploration
- Need for closure drives timing
- Alternatives unexplored
- First adequate option accepted
- Ambiguity resolved prematurely

When no premature closure:
- Exploration proportionate to stakes
- Timing appropriate to complexity
- Alternatives adequately considered
- Options compared before selection
- Ambiguity tolerated appropriately

Output JSON with: premature_closure_detected (bool), severity (none/mild/moderate/severe), exploration_truncation (what exploration truncated), need_for_closure (what closure need), satisficing_degradation (what satisficing degradation), recommendation (no_premature_closure/mild_exploration_extension/significant_alternative_search/major_decision_reopening/emergency_complete_premature_closure)."""

EPISTEMIC_DECISION_PREMATURE_CLOSURE_PROMPT = """Detect epistemic decision premature closure:

Decision timing: {decision_timing}
Exploration truncation: {exploration_truncation}
Need for closure: {need_for_closure}
Satisficing degradation: {satisficing_degradation}
Domain: {domain}
Context: {context}

Is the decision being made before adequate exploration? Return ONLY valid JSON."""


class EpistemicDecisionPrematureClosureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision_timing: str,
        *,
        exploration_truncation: str = "",
        need_for_closure: str = "",
        satisficing_degradation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_PREMATURE_CLOSURE_PROMPT.format(
                decision_timing=decision_timing,
                exploration_truncation=exploration_truncation or "Not specified",
                need_for_closure=need_for_closure or "Not specified",
                satisficing_degradation=satisficing_degradation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_PREMATURE_CLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision_timing": decision_timing[:200],
            "premature_closure_detected": data.get("premature_closure_detected", False),
            "severity": data.get("severity", ""),
            "exploration_truncation": data.get("exploration_truncation", ""),
            "need_for_closure": data.get("need_for_closure", ""),
            "satisficing_degradation": data.get("satisficing_degradation", ""),
            "recommendation": data.get("recommendation", ""),
        }
