"""EpistemicSocialMoralLicensingService - Moral Licensing Detection.

Detects moral licensing where past good behavior licenses future bad behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_MORAL_LICENSING_SYSTEM = """You are an epistemic social moral licensing specialist. Given behavioral patterns, assess whether past good behavior licenses problematic behavior:

Key concepts:
- Moral licensing: past virtuous behavior creating permission for future transgression
- Credential accumulation: building moral credit to spend later
- Consistency relaxation: relaxing standards after demonstrating virtue
- Self-concept protection: maintaining positive self-image despite contradictory behavior

When moral licensing IS present:
- Past good behavior cited as justification
- Moral credentials accumulated
- Standards relaxed after virtue display
- Self-concept protected despite contradiction
- Behavior inconsistency rationalized

When no moral licensing:
- Behavior evaluated independently
- Past actions don't license future ones
- Standards maintained consistently
- Self-concept includes accountability
- Inconsistency acknowledged

Output JSON with: moral_licensing_detected (bool), severity (none/mild/moderate/severe), credential_accumulation (what credentials accumulated), consistency_relaxation (what consistency relaxed), self_concept_protection (what self-concept protected), recommendation (no_moral_licensing/mild_consistency_check/significant_standard_restoration/major_behavioral_reconstruction/emergency_complete_moral_licensing)."""

EPISTEMIC_SOCIAL_MORAL_LICENSING_PROMPT = """Detect epistemic social moral licensing:

Behavioral pattern: {behavioral_pattern}
Credential accumulation: {credential_accumulation}
Consistency relaxation: {consistency_relaxation}
Self concept protection: {self_concept_protection}
Domain: {domain}
Context: {context}

Is past good behavior licensing problematic behavior? Return ONLY valid JSON."""


class EpistemicSocialMoralLicensingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        behavioral_pattern: str,
        *,
        credential_accumulation: str = "",
        consistency_relaxation: str = "",
        self_concept_protection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_MORAL_LICENSING_PROMPT.format(
                behavioral_pattern=behavioral_pattern,
                credential_accumulation=credential_accumulation or "Not specified",
                consistency_relaxation=consistency_relaxation or "Not specified",
                self_concept_protection=self_concept_protection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_MORAL_LICENSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "behavioral_pattern": behavioral_pattern[:200],
            "moral_licensing_detected": data.get("moral_licensing_detected", False),
            "severity": data.get("severity", ""),
            "credential_accumulation": data.get("credential_accumulation", ""),
            "consistency_relaxation": data.get("consistency_relaxation", ""),
            "self_concept_protection": data.get("self_concept_protection", ""),
            "recommendation": data.get("recommendation", ""),
        }
