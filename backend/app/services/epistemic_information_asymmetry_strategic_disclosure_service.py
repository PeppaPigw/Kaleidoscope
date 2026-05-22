"""EpistemicInformationAsymmetryStrategicDisclosureService — Epistemic Information Asymmetry Strategic Disclosure Detection.

Detects strategic information disclosure that distorts understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFORMATION_ASYMMETRY_STRATEGIC_DISCLOSURE_SYSTEM = """You are an epistemic information asymmetry strategic disclosure specialist. Given selective revelation, assess strategic information disclosure that distorts understanding:

Key concepts:
- Epistemic strategic disclosure: information is revealed selectively to shape conclusions while preserving plausible transparency
- Selective revelation: favorable, convenient, or partial information is disclosed while material context is withheld
- Timing manipulation: disclosure is delayed, accelerated, or sequenced to control interpretation
- Framing through omission: omitted context changes the meaning of what is disclosed
- Disclosure theater: performative transparency creates an impression of openness without enabling understanding

When strategic disclosure IS present:
- Disclosure is selective or sequenced to steer interpretation
- Relevant context is withheld
- Timing shapes perceived significance
- Transparency is performative rather than informative
- Understanding is distorted by what is omitted

When no strategic disclosure:
- Disclosure includes material context
- Timing does not manipulate interpretation
- Omissions are justified and visible
- Transparency enables independent assessment

Output JSON with: strategic_disclosure_detected (bool), severity (none/mild/moderate/severe), timing_manipulation (how timing distorts understanding), framing_through_omission (what omitted context changes), disclosure_theater (how transparency is performative), recommendation (no_strategic_disclosure/mild_context_completion/significant_disclosure_audit/major_transparency_redesign/emergency_disclosure_manipulation_containment)."""

EPISTEMIC_INFORMATION_ASYMMETRY_STRATEGIC_DISCLOSURE_PROMPT = """Detect epistemic information asymmetry strategic disclosure:

Selective revelation: {selective_revelation}
Timing manipulation: {timing_manipulation}
Framing through omission: {framing_through_omission}
Disclosure theater: {disclosure_theater}
Domain: {domain}
Context: {context}

Is strategic information disclosure distorting understanding? Return ONLY valid JSON."""


class EpistemicInformationAsymmetryStrategicDisclosureService:
    """Detects epistemic information asymmetry strategic disclosure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        selective_revelation: str,
        *,
        timing_manipulation: str = "",
        framing_through_omission: str = "",
        disclosure_theater: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic information asymmetry strategic disclosure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFORMATION_ASYMMETRY_STRATEGIC_DISCLOSURE_PROMPT.format(
                selective_revelation=selective_revelation,
                timing_manipulation=timing_manipulation or "Not specified",
                framing_through_omission=framing_through_omission or "Not specified",
                disclosure_theater=disclosure_theater or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFORMATION_ASYMMETRY_STRATEGIC_DISCLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "selective_revelation": selective_revelation[:200],
            "strategic_disclosure_detected": data.get("strategic_disclosure_detected", False),
            "severity": data.get("severity", ""),
            "timing_manipulation": data.get("timing_manipulation", ""),
            "framing_through_omission": data.get("framing_through_omission", ""),
            "disclosure_theater": data.get("disclosure_theater", ""),
            "recommendation": data.get("recommendation", ""),
        }
