"""EpistemicCounterfactualNormViolationService — Epistemic Counterfactual Norm Violation Detection.

Detects epistemic counterfactual norm violation — focusing counterfactual reasoning
on norm-violating events while ignoring equally causal norm-conforming factors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_NORM_VIOLATION_SYSTEM = """You are an epistemic counterfactual norm violation specialist. Given norm-focused counterfactuals, assess distortion:

Key concepts:
- Epistemic counterfactual norm violation: focusing on norm-breaking as cause
- Abnormal focus: counterfactuals targeting unusual rather than causal events
- Moral counterfactual: generating alternatives only for morally wrong actions
- Routine blindness: ignoring routine factors that were equally causal
- Exception fixation: treating exceptions as more causal than regularities
- Blame-seeking counterfactual: alternatives designed to assign blame
- Controllability bias: focusing on controllable factors over uncontrollable

When epistemic counterfactual norm violation IS present:
- Norm-breaking focused on
- Unusual events targeted
- Moral wrongs as counterfactual focus
- Routine factors ignored
- Exceptions treated as more causal
- Blame-seeking alternatives
- Controllable factors overweighted

When no norm violation bias:
- Causal factors weighted by relevance
- Unusual and routine both considered
- Moral and amoral factors included
- All causal factors assessed
- Exceptions and regularities balanced
- Alternatives not blame-seeking
- Controllability not overweighted

Output JSON with: norm_violation_detected (bool), severity (none/mild/moderate/severe), abnormal_focus (what unusual events targeted), moral_counterfactual (what moral wrongs focused), routine_blindness (what routine factors ignored), blame_seeking (what blame-seeking alternatives), recommendation (no_norm_violation/mild_causal_broadening/significant_routine_inclusion/major_intensive_causal_analysis/emergency_complete_norm_violation)."""

EPISTEMIC_COUNTERFACTUAL_NORM_VIOLATION_PROMPT = """Detect epistemic counterfactual norm violation:

Abnormal focus: {abnormal_focus}
Moral counterfactual: {moral_counterfactual}
Routine blindness: {routine_blindness}
Blame seeking: {blame_seeking}
Domain: {domain}
Context: {context}

Are counterfactuals focusing on norm-violating events over equally causal factors? Return ONLY valid JSON."""


class EpistemicCounterfactualNormViolationService:
    """Detects epistemic counterfactual norm violation — norm-focused alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        abnormal_focus: str,
        *,
        moral_counterfactual: str = "",
        routine_blindness: str = "",
        blame_seeking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual norm violation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_NORM_VIOLATION_PROMPT.format(
                abnormal_focus=abnormal_focus,
                moral_counterfactual=moral_counterfactual or "Not specified",
                routine_blindness=routine_blindness or "Not specified",
                blame_seeking=blame_seeking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_NORM_VIOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "abnormal_focus": abnormal_focus[:200],
            "norm_violation_detected": data.get("norm_violation_detected", False),
            "severity": data.get("severity", ""),
            "moral_counterfactual": data.get("moral_counterfactual", ""),
            "routine_blindness": data.get("routine_blindness", ""),
            "blame_seeking": data.get("blame_seeking", ""),
            "recommendation": data.get("recommendation", ""),
        }
