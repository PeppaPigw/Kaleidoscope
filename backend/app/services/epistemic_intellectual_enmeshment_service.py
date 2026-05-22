"""EpistemicIntellectualEnmeshmentService — Epistemic Intellectual Enmeshment Detection.

Detects epistemic intellectual enmeshment — enmeshment where intellectual
identity becomes fused with another's.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_ENMESHMENT_SYSTEM = """You are an epistemic intellectual enmeshment specialist. Given intellectual identity fusion, assess enmeshment:

Key concepts:
- Epistemic intellectual enmeshment: intellectual identity fused with another's
- Thought twinning: thinking must match another person's exactly
- Intellectual symbiosis: can't form views without the other
- Belief mirroring: automatically adopting another's positions
- Cognitive dependency: needing another to validate all thoughts
- Identity merger: intellectual self defined only through another
- Differentiation failure: unable to hold different views from partner

When epistemic intellectual enmeshment IS present:
- Intellectual identity fused with another's
- Thinking must match another's
- Can't form views without the other
- Automatically adopting positions
- Needing validation for all thoughts
- Self defined only through another
- Unable to hold different views

When no intellectual enmeshment:
- Separate intellectual identity
- Independent thinking
- Self-sufficient view formation
- Deliberate position adoption
- Self-validated thoughts
- Self-defined intellectually
- Comfortable with differences

Output JSON with: intellectual_enmeshment_detected (bool), severity (none/mild/moderate/severe), thought_twinning (what must match), intellectual_symbiosis (what can't form without), belief_mirroring (what automatically adopting), differentiation_failure (what unable to differ on), recommendation (no_intellectual_enmeshment/mild_differentiation_practice/significant_separation_work/major_intensive_individuation/emergency_complete_fusion)."""

EPISTEMIC_INTELLECTUAL_ENMESHMENT_PROMPT = """Detect epistemic intellectual enmeshment:

Thought twinning: {thought_twinning}
Intellectual symbiosis: {intellectual_symbiosis}
Belief mirroring: {belief_mirroring}
Differentiation failure: {differentiation_failure}
Domain: {domain}
Context: {context}

Is there intellectual identity becoming fused with another's? Return ONLY valid JSON."""


class EpistemicIntellectualEnmeshmentService:
    """Detects epistemic intellectual enmeshment — intellectual identity fused with another's."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thought_twinning: str,
        *,
        intellectual_symbiosis: str = "",
        belief_mirroring: str = "",
        differentiation_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual enmeshment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_ENMESHMENT_PROMPT.format(
                thought_twinning=thought_twinning,
                intellectual_symbiosis=intellectual_symbiosis or "Not specified",
                belief_mirroring=belief_mirroring or "Not specified",
                differentiation_failure=differentiation_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_ENMESHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thought_twinning": thought_twinning[:200],
            "intellectual_enmeshment_detected": data.get("intellectual_enmeshment_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_symbiosis": data.get("intellectual_symbiosis", ""),
            "belief_mirroring": data.get("belief_mirroring", ""),
            "differentiation_failure": data.get("differentiation_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
