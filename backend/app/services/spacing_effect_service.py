"""SpacingEffectService — Spacing Effect Detection.

Detects spacing effect violations — failing to leverage spaced
repetition for better retention. Ebbinghaus (1885), Cepeda et al.
(2006). Information reviewed at increasing intervals is retained
far better than information crammed in a single session. Massed
practice feels productive but produces inferior long-term retention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SPACING_EFFECT_SYSTEM = """You are a spacing effect specialist. Given a learning or information retention situation, assess whether spacing principles are being violated:

Key concepts (Ebbinghaus, 1885; Cepeda et al., 2006):
- Spacing effect: distributed practice beats massed practice
- Forgetting curve: memory decays exponentially without review
- Desirable difficulty: spacing feels harder but produces better retention
- Illusion of competence: massed practice creates false confidence
- Interleaving benefit: mixing topics during spaced sessions
- Lag effect: longer spacing intervals produce better long-term retention
- Testing effect interaction: spaced retrieval practice is optimal

When spacing violations ARE present:
- Cramming all learning into single sessions
- No review schedule for important information
- Assuming one exposure is sufficient for retention
- Massed practice creating illusion of mastery
- No systematic revisiting of key decisions or findings
- Information overload in single sessions without follow-up
- Relying on recognition rather than recall

When the approach IS appropriate:
- Time constraints genuinely prevent spacing
- The information only needs short-term retention
- Active retrieval practice is being used within sessions
- A spaced review system is already in place
- The material is being applied immediately and repeatedly

Output JSON with: spacing_violation_present (bool), severity (none/mild/moderate/severe), situation (what learning/retention context), current_approach (how information is being processed), spacing_gap (what spacing is missing), retention_risk (what is likely to be forgotten), false_confidence (is massed practice creating illusion of mastery), optimal_schedule (what spacing would be better), recommendation (spacing_appropriate/mild_massing_tendency/significant_spacing_violation/major_cramming_pattern/implement_spaced_review)."""

SPACING_EFFECT_PROMPT = """Detect spacing effect violations:

Situation: {situation}
Learning approach: {approach}
Review schedule: {schedule}
Retention needs: {retention}
Domain: {domain}
Context: {context}

Is information being processed without appropriate spacing, risking poor long-term retention? Return ONLY valid JSON."""


class SpacingEffectService:
    """Detects spacing effect violations — failing to use spaced repetition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        approach: str = "",
        schedule: str = "",
        retention: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect spacing effect violations."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPACING_EFFECT_PROMPT.format(
                situation=situation,
                approach=approach or "Not specified",
                schedule=schedule or "Not specified",
                retention=retention or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SPACING_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "spacing_violation_present": data.get("spacing_violation_present", False),
            "severity": data.get("severity", ""),
            "current_approach": data.get("current_approach", ""),
            "spacing_gap": data.get("spacing_gap", ""),
            "retention_risk": data.get("retention_risk", ""),
            "false_confidence": data.get("false_confidence", ""),
            "optimal_schedule": data.get("optimal_schedule", ""),
            "recommendation": data.get("recommendation", ""),
        }
