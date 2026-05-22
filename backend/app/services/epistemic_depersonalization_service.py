"""EpistemicDepersonalizationService — Epistemic Depersonalization Detection.

Detects epistemic depersonalization — feeling detached from one's own
intellectual processes, as if observing one's thinking from outside.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEPERSONALIZATION_SYSTEM = """You are an epistemic depersonalization specialist. Given detachment from own thinking, assess depersonalization:

Key concepts:
- Epistemic depersonalization: detached from own intellectual processes
- Observer stance: watching own thinking from outside
- Ownership loss: thoughts don't feel like mine
- Automaticity: thinking happening without felt agency
- Unreality of self: intellectual self feels unreal
- Emotional numbing: no feeling about own ideas
- Alienation: estranged from own intellectual life

When epistemic depersonalization IS present:
- Detached from own processes
- Watching from outside
- Thoughts don't feel mine
- Thinking without agency
- Intellectual self unreal
- No feeling about ideas
- Estranged from own thinking

When no depersonalization:
- Connected to processes
- Inside own thinking
- Thoughts feel owned
- Agentic thinking
- Real intellectual self
- Feeling about ideas
- At home in thinking

Output JSON with: depersonalization_detected (bool), severity (none/mild/moderate/severe), observer_stance (what watching from outside), ownership_loss (what not feeling mine), automaticity_level (what without agency), alienation_pattern (what estranged from), recommendation (no_depersonalization/mild_grounding_practice/significant_reconnection_therapy/major_intensive_integration/emergency_severe_depersonalization)."""

EPISTEMIC_DEPERSONALIZATION_PROMPT = """Detect epistemic depersonalization:

Observer stance: {observer_stance}
Ownership loss: {ownership_loss}
Automaticity level: {automaticity_level}
Alienation pattern: {alienation_pattern}
Domain: {domain}
Context: {context}

Is there feeling detached from one's own intellectual processes? Return ONLY valid JSON."""


class EpistemicDepersonalizationService:
    """Detects epistemic depersonalization — detached from own thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        observer_stance: str,
        *,
        ownership_loss: str = "",
        automaticity_level: str = "",
        alienation_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic depersonalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEPERSONALIZATION_PROMPT.format(
                observer_stance=observer_stance,
                ownership_loss=ownership_loss or "Not specified",
                automaticity_level=automaticity_level or "Not specified",
                alienation_pattern=alienation_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEPERSONALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "observer_stance": observer_stance[:200],
            "depersonalization_detected": data.get("depersonalization_detected", False),
            "severity": data.get("severity", ""),
            "ownership_loss": data.get("ownership_loss", ""),
            "automaticity_level": data.get("automaticity_level", ""),
            "alienation_pattern": data.get("alienation_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
