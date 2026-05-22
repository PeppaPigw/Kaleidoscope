"""InstitutionalCaptureService — Institutional Capture Detection.

Detects institutional capture — when institutions meant to regulate
or serve the public become captured by those they regulate or
special interests, distorting their original mission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INSTITUTIONAL_CAPTURE_SYSTEM = """You are an institutional capture specialist. Given an institutional situation, assess whether the institution has been captured by those it should regulate or serve:

Key concepts:
- Regulatory capture: regulators serving regulated industry
- Mission drift: institution drifting from original purpose
- Revolving door: personnel moving between regulator and regulated
- Information asymmetry: regulated entities controlling information
- Resource dependence: institution dependent on those it oversees
- Cultural capture: adopting worldview of regulated entities
- Stakeholder capture: one stakeholder dominating institution

When institutional capture IS present:
- Institution's actions primarily benefit those it should regulate
- Revolving door between institution and regulated entities
- Information controlled by regulated entities
- Institution dependent on regulated entities for resources
- Original mission subordinated to captured interests
- Dissent within institution suppressed
- Public interest systematically deprioritized

When institution is independent:
- Actions aligned with original mission
- Independence from regulated entities maintained
- Multiple information sources used
- Resources independent of regulated entities
- Public interest consistently prioritized
- Internal dissent welcomed
- Accountability to original mission maintained

Output JSON with: capture_present (bool), severity (none/mild/moderate/severe), institution (what institution), captured_by (who has captured it), mechanism (how capture occurred), mission_drift (how original mission is distorted), recommendation (independent_institution/mild_influence/significant_capture/major_regulatory_capture/restore_independence)."""

INSTITUTIONAL_CAPTURE_PROMPT = """Detect institutional capture:

Institution: {institution}
Mission: {mission}
Actions: {actions}
Relationships: {relationships}
Domain: {domain}
Context: {context}

Has this institution been captured by those it should regulate or serve? Return ONLY valid JSON."""


class InstitutionalCaptureService:
    """Detects institutional capture — institutions serving those they should regulate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        institution: str,
        *,
        mission: str = "",
        actions: str = "",
        relationships: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect institutional capture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INSTITUTIONAL_CAPTURE_PROMPT.format(
                institution=institution,
                mission=mission or "Not specified",
                actions=actions or "Not specified",
                relationships=relationships or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INSTITUTIONAL_CAPTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "institution": institution[:200],
            "capture_present": data.get("capture_present", False),
            "severity": data.get("severity", ""),
            "captured_by": data.get("captured_by", ""),
            "mechanism": data.get("mechanism", ""),
            "mission_drift": data.get("mission_drift", ""),
            "recommendation": data.get("recommendation", ""),
        }
