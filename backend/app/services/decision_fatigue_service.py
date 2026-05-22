"""DecisionFatigueService — Decision Fatigue Detection.

Detects decision fatigue — when the accumulation of decisions
degrades the quality of subsequent choices. As cognitive
resources deplete, people default to easier options, avoid
decisions, or make impulsive choices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECISION_FATIGUE_SYSTEM = """You are a decision fatigue specialist. Given a decision context, assess whether fatigue is degrading decision quality:

Key concepts:
- Decision fatigue: quality degrades with number of prior decisions
- Ego depletion: willpower as limited resource
- Decision avoidance: choosing not to choose
- Default escalation: increasingly accepting defaults as fatigue grows
- Simplification: reducing complex decisions to simple heuristics
- Time-of-day effects: decision quality varies with energy
- Decision load: cumulative burden of choices

When decision fatigue IS present:
- Decision quality declining over a sequence of choices
- Increasing tendency to accept defaults or avoid choosing
- Complex decisions simplified inappropriately
- Impulsive choices replacing deliberate ones
- Decision avoidance or deferral increasing
- Heuristics replacing analysis as fatigue grows
- Important decisions made after many prior decisions

When decision fatigue is NOT present:
- Decision quality maintained regardless of prior load
- Important decisions scheduled when fresh
- Decision load managed through batching or delegation
- Breaks taken between important decisions
- Awareness of fatigue effects and compensation
- Trivial decisions automated to preserve capacity
- Energy and attention matched to decision importance

Output JSON with: fatigue_present (bool), severity (none/mild/moderate/severe), decision_load (how many prior decisions), quality_indicators (signs of degraded quality), timing (when in sequence this decision falls), mitigation (what could reduce fatigue), recommendation (no_fatigue/mild_depletion/significant_fatigue/major_quality_degradation/reschedule_or_simplify)."""

DECISION_FATIGUE_PROMPT = """Detect decision fatigue:

Decision: {decision}
Prior decisions: {prior_decisions}
Time context: {timing}
Quality indicators: {quality}
Domain: {domain}
Context: {context}

Is decision fatigue degrading the quality of this choice? Return ONLY valid JSON."""


class DecisionFatigueService:
    """Detects decision fatigue — accumulated decisions degrading quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        prior_decisions: str = "",
        timing: str = "",
        quality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect decision fatigue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECISION_FATIGUE_PROMPT.format(
                decision=decision,
                prior_decisions=prior_decisions or "Not specified",
                timing=timing or "Not specified",
                quality=quality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DECISION_FATIGUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "fatigue_present": data.get("fatigue_present", False),
            "severity": data.get("severity", ""),
            "decision_load": data.get("decision_load", ""),
            "quality_indicators": data.get("quality_indicators", ""),
            "mitigation": data.get("mitigation", ""),
            "recommendation": data.get("recommendation", ""),
        }
