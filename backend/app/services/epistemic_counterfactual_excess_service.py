"""EpistemicCounterfactualExcessService — Epistemic Counterfactual Excess Detection.

Detects epistemic counterfactual excess — excessive counterfactual thinking
that paralyzes action through endless what-if scenarios.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_EXCESS_SYSTEM = """You are an epistemic counterfactual excess specialist. Given excessive counterfactual thinking, assess counterfactual excess:

Key concepts:
- Epistemic counterfactual excess: excessive what-if thinking paralyzing action
- Analysis paralysis: too many counterfactuals preventing decision
- Regret spiraling: spiraling through what-could-have-been
- Possibility explosion: considering too many possibilities
- Decision avoidance: using counterfactuals to avoid committing
- Perfectionism through counterfactuals: no option good enough because alternatives exist
- Rumination disguised as analysis: ruminating while pretending to analyze

When epistemic counterfactual excess IS present:
- Excessive what-if thinking
- Action paralyzed
- Regret spiraling
- Too many possibilities considered
- Decisions avoided
- No option good enough
- Rumination disguised as analysis

When no counterfactual excess:
- Counterfactuals used productively
- Action taken despite uncertainty
- Regret processed healthily
- Possibilities bounded appropriately
- Decisions made timely
- Good-enough accepted
- Analysis genuine

Output JSON with: counterfactual_excess_detected (bool), severity (none/mild/moderate/severe), analysis_paralysis (what paralyzed), regret_spiraling (what regret about), possibility_explosion (what possibilities overwhelming), decision_avoidance (what decisions avoided), recommendation (no_counterfactual_excess/mild_bounding_practice/significant_action_recovery/major_intensive_commitment_training/emergency_complete_counterfactual_excess)."""

EPISTEMIC_COUNTERFACTUAL_EXCESS_PROMPT = """Detect epistemic counterfactual excess:

Analysis paralysis: {analysis_paralysis}
Regret spiraling: {regret_spiraling}
Possibility explosion: {possibility_explosion}
Decision avoidance: {decision_avoidance}
Domain: {domain}
Context: {context}

Is excessive counterfactual thinking paralyzing action? Return ONLY valid JSON."""


class EpistemicCounterfactualExcessService:
    """Detects epistemic counterfactual excess — what-if paralysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis_paralysis: str,
        *,
        regret_spiraling: str = "",
        possibility_explosion: str = "",
        decision_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual excess."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_EXCESS_PROMPT.format(
                analysis_paralysis=analysis_paralysis,
                regret_spiraling=regret_spiraling or "Not specified",
                possibility_explosion=possibility_explosion or "Not specified",
                decision_avoidance=decision_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_EXCESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis_paralysis": analysis_paralysis[:200],
            "counterfactual_excess_detected": data.get("counterfactual_excess_detected", False),
            "severity": data.get("severity", ""),
            "regret_spiraling": data.get("regret_spiraling", ""),
            "possibility_explosion": data.get("possibility_explosion", ""),
            "decision_avoidance": data.get("decision_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
