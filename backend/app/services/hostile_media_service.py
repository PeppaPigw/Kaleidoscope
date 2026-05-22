"""HostileMediaService — Hostile Media Effect Detection.

Detects hostile media effect — perceiving neutral or balanced
media coverage as biased against one's own position. Vallone,
Ross & Lepper (1985). Both sides of a conflict perceive the
same coverage as biased against them. Leads to distrust of
media, echo chamber reinforcement, and inability to recognize
balanced reporting.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HOSTILE_MEDIA_SYSTEM = """You are a hostile media effect specialist. Given a perception of media bias, assess whether the perception reflects actual bias or the hostile media effect:

Key concepts (Vallone, Ross & Lepper, 1985):
- Hostile media effect: partisans perceive neutral coverage as biased against them
- Relative hostile media effect: own side's coverage seen as less favorable
- Selective categorization: classifying ambiguous content as hostile
- Different standards: applying stricter standards to coverage of own position
- Prior attitude effect: existing beliefs color perception of neutrality
- Assimilation/contrast: interpreting same content differently based on position
- Third-person effect: believing others are more influenced by biased media

When hostile media effect IS present:
- Both sides perceive the same coverage as biased against them
- Neutral reporting perceived as hostile to one's position
- "They always cover the other side more favorably"
- Balanced coverage dismissed as "false balance" or "bias"
- Applying different standards to coverage of own vs. other position
- Perceiving factual reporting as editorial bias

When the media IS actually biased:
- Systematic content analysis confirms asymmetric coverage
- Multiple independent observers agree on the direction of bias
- The coverage demonstrably omits relevant facts favoring one side
- Framing consistently favors one interpretation
- Source selection is systematically skewed
- The bias is documented, not just perceived by partisans

Output JSON with: hostile_media_present (bool), severity (none/mild/moderate/severe), coverage (what coverage is being evaluated), perception (how is it perceived), actual_balance (what is the actual balance of the coverage?), partisan_position (what is the perceiver's position?), both_sides_perceive_bias (bool — do both sides see it as biased?), standards_applied (are different standards applied to own vs other side?), evidence_of_actual_bias (what evidence exists for real bias?), recommendation (bias_real/mild_hostile_perception/significant_hostile_media/major_hostile_media_effect/evaluate_coverage_objectively)."""

HOSTILE_MEDIA_PROMPT = """Detect hostile media effect:

Coverage: {coverage}
Perception: {perception}
Position: {position}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is the perception of bias reflecting actual bias or the hostile media effect? Return ONLY valid JSON."""


class HostileMediaService:
    """Detects hostile media effect — perceiving neutral coverage as biased."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        coverage: str,
        *,
        perception: str = "",
        position: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hostile media effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HOSTILE_MEDIA_PROMPT.format(
                coverage=coverage,
                perception=perception or "Not specified",
                position=position or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HOSTILE_MEDIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "coverage": coverage[:200],
            "hostile_media_present": data.get("hostile_media_present", False),
            "severity": data.get("severity", ""),
            "actual_balance": data.get("actual_balance", ""),
            "partisan_position": data.get("partisan_position", ""),
            "both_sides_perceive_bias": data.get("both_sides_perceive_bias", False),
            "standards_applied": data.get("standards_applied", ""),
            "evidence_of_actual_bias": data.get("evidence_of_actual_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
