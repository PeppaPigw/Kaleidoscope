"""EpistemicMoralInjuryService — Epistemic Moral Injury Detection.

Detects epistemic moral injury — deep wound from violation of intellectual
values, witnessing or participating in intellectual betrayal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MORAL_INJURY_SYSTEM = """You are an epistemic moral injury specialist. Given intellectual values violation, assess moral injury:

Key concepts:
- Epistemic moral injury: wound from intellectual values violation
- Betrayal: trusted authority violated intellectual principles
- Perpetration: participated in intellectual wrongdoing
- Witness: observed intellectual injustice without acting
- Guilt: responsibility for intellectual harm
- Shame: fundamental unworthiness from violation
- Meaning collapse: loss of intellectual moral framework

When epistemic moral injury IS present:
- Wound from values violation
- Authority violated principles
- Participated in wrongdoing
- Observed injustice passively
- Responsibility for harm
- Fundamental unworthiness
- Moral framework collapsed

When no moral injury:
- Values intact
- Authority trustworthy
- No wrongdoing participation
- Acted on injustice
- No harmful responsibility
- Worthy self-concept
- Moral framework intact

Output JSON with: moral_injury_detected (bool), severity (none/mild/moderate/severe), violation_type (what values betrayed), perpetration_role (what participation), guilt_level (what responsibility), meaning_impact (what framework collapse), recommendation (no_moral_injury/mild_values_clarification/significant_moral_repair/major_intensive_therapy/emergency_severe_collapse)."""

EPISTEMIC_MORAL_INJURY_PROMPT = """Detect epistemic moral injury:

Violation type: {violation_type}
Perpetration role: {perpetration_role}
Guilt level: {guilt_level}
Meaning impact: {meaning_impact}
Domain: {domain}
Context: {context}

Is there deep wound from violation of intellectual values or participation in betrayal? Return ONLY valid JSON."""


class EpistemicMoralInjuryService:
    """Detects epistemic moral injury — intellectual values violation wound."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        violation_type: str,
        *,
        perpetration_role: str = "",
        guilt_level: str = "",
        meaning_impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic moral injury."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MORAL_INJURY_PROMPT.format(
                violation_type=violation_type,
                perpetration_role=perpetration_role or "Not specified",
                guilt_level=guilt_level or "Not specified",
                meaning_impact=meaning_impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MORAL_INJURY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "violation_type": violation_type[:200],
            "moral_injury_detected": data.get("moral_injury_detected", False),
            "severity": data.get("severity", ""),
            "perpetration_role": data.get("perpetration_role", ""),
            "guilt_level": data.get("guilt_level", ""),
            "meaning_impact": data.get("meaning_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
