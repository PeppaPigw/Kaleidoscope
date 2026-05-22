"""LegibilityBiasService — Legibility Bias Detection.

Detects legibility bias — preferring solutions that are legible,
measurable, and easy to understand over solutions that are more
effective but harder to measure or explain. Scott (1998). States
and organizations prefer legible systems they can monitor and
control, even when illegible systems work better.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LEGIBILITY_BIAS_SYSTEM = """You are a legibility bias specialist. Given a decision between approaches, assess whether legibility is being privileged over effectiveness:

Key concepts (Scott, 1998):
- Legibility bias: preferring measurable over effective
- High modernism: imposing legible order on complex systems
- Metis: local, practical knowledge that resists formalization
- Seeing like a state: simplifying for administrative convenience
- Dashboard tyranny: managing by what's visible on dashboards
- Formalization premium: valuing formal over informal knowledge
- Measurement as control: measuring to control, not to understand

When legibility bias IS present:
- Choosing measurable KPIs over unmeasurable but important outcomes
- Preferring formal processes over effective informal ones
- Standardizing systems that work better with local adaptation
- "If we can't measure it, we can't manage it" (ignoring unmeasurables)
- Replacing effective tacit knowledge with inferior explicit procedures
- Choosing legible but worse solutions over opaque but better ones
- Administrative convenience trumping actual effectiveness

When legibility preference IS appropriate:
- Accountability genuinely requires measurement
- The legible solution is also the most effective
- Transparency serves important governance functions
- The domain genuinely benefits from standardization
- Measurement enables genuine improvement
- Both legibility and effectiveness are optimized together

Output JSON with: legibility_bias_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), legible_option (what is the legible/measurable option), effective_option (what is the more effective but less legible option), legibility_premium (how much effectiveness is sacrificed for legibility), measurement_value (does measurement actually help here), local_knowledge_lost (what tacit knowledge is being discarded), recommendation (legibility_appropriate/mild_measurement_preference/significant_legibility_bias/major_effectiveness_sacrifice/optimize_for_outcomes_not_legibility)."""

LEGIBILITY_BIAS_PROMPT = """Detect legibility bias:

Decision: {decision}
Legible option: {legible}
Effective option: {effective}
Trade-off: {tradeoff}
Domain: {domain}
Context: {context}

Is legibility/measurability being privileged over actual effectiveness? Return ONLY valid JSON."""


class LegibilityBiasService:
    """Detects legibility bias — preferring measurable over effective."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        legible: str = "",
        effective: str = "",
        tradeoff: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect legibility bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LEGIBILITY_BIAS_PROMPT.format(
                decision=decision,
                legible=legible or "Not specified",
                effective=effective or "Not specified",
                tradeoff=tradeoff or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LEGIBILITY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "legibility_bias_present": data.get("legibility_bias_present", False),
            "severity": data.get("severity", ""),
            "legible_option": data.get("legible_option", ""),
            "effective_option": data.get("effective_option", ""),
            "legibility_premium": data.get("legibility_premium", ""),
            "measurement_value": data.get("measurement_value", ""),
            "local_knowledge_lost": data.get("local_knowledge_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
