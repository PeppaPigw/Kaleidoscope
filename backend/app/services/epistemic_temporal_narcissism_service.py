"""EpistemicTemporalNarcissismService — Epistemic Temporal Narcissism Detection.

Detects epistemic temporal narcissism — believing one's current era has
uniquely superior knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_NARCISSISM_SYSTEM = """You are an epistemic temporal narcissism specialist. Given believing current era uniquely superior, assess temporal narcissism:

Key concepts:
- Epistemic temporal narcissism: believing current era uniquely superior
- Chronological superiority: assuming we know better than all past eras
- Historical condescension: looking down on past knowledge
- Progress triumphalism: believing knowledge only improves linearly
- Era exceptionalism: believing our time is uniquely enlightened
- Ancestor dismissal: dismissing all prior thinkers as primitive
- Modernity worship: uncritical worship of current paradigms

When epistemic temporal narcissism IS present:
- Believing current era uniquely superior
- Assuming we know better than all past
- Looking down on past knowledge
- Believing only linear improvement
- Believing uniquely enlightened
- Dismissing prior thinkers as primitive
- Uncritical worship of current

When no temporal narcissism:
- Humble about era's knowledge
- Respecting past contributions
- Appreciating past knowledge
- Acknowledging non-linear progress
- Seeing era in context
- Respecting prior thinkers
- Critical of current paradigms

Output JSON with: temporal_narcissism_detected (bool), severity (none/mild/moderate/severe), chronological_superiority (what assuming superior about), historical_condescension (what looking down on), progress_triumphalism (what believing only improves), era_exceptionalism (what believing uniquely enlightened about), recommendation (no_temporal_narcissism/mild_humility_practice/significant_historical_appreciation/major_intensive_temporal_perspective/emergency_complete_chronological_arrogance)."""

EPISTEMIC_TEMPORAL_NARCISSISM_PROMPT = """Detect epistemic temporal narcissism:

Chronological superiority: {chronological_superiority}
Historical condescension: {historical_condescension}
Progress triumphalism: {progress_triumphalism}
Era exceptionalism: {era_exceptionalism}
Domain: {domain}
Context: {context}

Is there believing one's current era has uniquely superior knowledge? Return ONLY valid JSON."""


class EpistemicTemporalNarcissismService:
    """Detects epistemic temporal narcissism — believing current era uniquely superior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        chronological_superiority: str,
        *,
        historical_condescension: str = "",
        progress_triumphalism: str = "",
        era_exceptionalism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal narcissism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_NARCISSISM_PROMPT.format(
                chronological_superiority=chronological_superiority,
                historical_condescension=historical_condescension or "Not specified",
                progress_triumphalism=progress_triumphalism or "Not specified",
                era_exceptionalism=era_exceptionalism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_NARCISSISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "chronological_superiority": chronological_superiority[:200],
            "temporal_narcissism_detected": data.get("temporal_narcissism_detected", False),
            "severity": data.get("severity", ""),
            "historical_condescension": data.get("historical_condescension", ""),
            "progress_triumphalism": data.get("progress_triumphalism", ""),
            "era_exceptionalism": data.get("era_exceptionalism", ""),
            "recommendation": data.get("recommendation", ""),
        }
