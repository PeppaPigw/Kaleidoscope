"""EpistemicAnalogyFalsePrecedentService — Epistemic Analogy False Precedent Detection.

Detects epistemic analogy false precedent — using historical analogies that differ
in crucial ways from the current situation, creating misleading parallels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_FALSE_PRECEDENT_SYSTEM = """You are an epistemic analogy false precedent specialist. Given historical analogies, assess precedent validity:

Key concepts:
- Epistemic false precedent: historical parallels that differ crucially
- Context stripping: removing context that makes precedent inapplicable
- Selective history: choosing precedents that support desired conclusion
- Crucial difference blindness: ignoring key differences between then and now
- Outcome projection: assuming same outcome because of surface similarity
- Era conflation: ignoring how changed conditions invalidate precedent
- Precedent shopping: searching for any historical case that supports position

When epistemic false precedent IS present:
- Historical parallels differ crucially
- Context stripped from precedent
- Precedents selectively chosen
- Key differences ignored
- Outcomes projected from surface similarity
- Changed conditions ignored
- Precedents shopped for

When no false precedent:
- Historical parallels structurally valid
- Context preserved
- Precedents representative
- Key differences acknowledged
- Outcomes not assumed
- Changed conditions assessed
- Precedents fairly selected

Output JSON with: false_precedent_detected (bool), severity (none/mild/moderate/severe), context_stripping (what context stripped), crucial_difference_blindness (what differences ignored), outcome_projection (what outcomes projected), precedent_shopping (what precedents shopped), recommendation (no_false_precedent/mild_difference_checking/significant_context_restoration/major_intensive_precedent_analysis/emergency_complete_false_precedent)."""

EPISTEMIC_ANALOGY_FALSE_PRECEDENT_PROMPT = """Detect epistemic analogy false precedent:

Context stripping: {context_stripping}
Crucial difference blindness: {crucial_difference_blindness}
Outcome projection: {outcome_projection}
Precedent shopping: {precedent_shopping}
Domain: {domain}
Context: {context}

Are historical analogies being used that differ in crucial ways? Return ONLY valid JSON."""


class EpistemicAnalogyFalsePrecedentService:
    """Detects epistemic analogy false precedent — misleading historical parallels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        context_stripping: str,
        *,
        crucial_difference_blindness: str = "",
        outcome_projection: str = "",
        precedent_shopping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy false precedent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_FALSE_PRECEDENT_PROMPT.format(
                context_stripping=context_stripping,
                crucial_difference_blindness=crucial_difference_blindness or "Not specified",
                outcome_projection=outcome_projection or "Not specified",
                precedent_shopping=precedent_shopping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_FALSE_PRECEDENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "context_stripping": context_stripping[:200],
            "false_precedent_detected": data.get("false_precedent_detected", False),
            "severity": data.get("severity", ""),
            "crucial_difference_blindness": data.get("crucial_difference_blindness", ""),
            "outcome_projection": data.get("outcome_projection", ""),
            "precedent_shopping": data.get("precedent_shopping", ""),
            "recommendation": data.get("recommendation", ""),
        }
