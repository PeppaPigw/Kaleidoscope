"""EpistemicInstitutionalRegulatoryCaptureService - Regulatory Capture Detection.

Detects regulatory capture where regulators serve regulated industry interests.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_REGULATORY_CAPTURE_SYSTEM = """You are an epistemic institutional regulatory capture specialist. Given regulatory behavior, assess whether regulators serve regulated industry interests:

Key concepts:
- Regulatory capture: regulators acting in interest of regulated industry rather than public
- Revolving door: personnel movement between regulator and industry
- Industry framing adoption: regulator adopting industry's problem definitions
- Public interest displacement: public good subordinated to industry convenience

When regulatory capture IS present:
- Regulator serves industry over public
- Revolving door patterns evident
- Industry framing adopted uncritically
- Public interest systematically displaced
- Enforcement selectively weakened

When no regulatory capture:
- Regulator maintains independence
- Public interest prioritized
- Industry input balanced with other stakeholders
- Enforcement consistent and robust
- Institutional boundaries maintained

Output JSON with: regulatory_capture_detected (bool), severity (none/mild/moderate/severe), revolving_door_pattern (what revolving door), industry_framing_adoption (what framing adopted), public_interest_displacement (what public interest displaced), recommendation (no_regulatory_capture/mild_independence_check/significant_boundary_restoration/major_institutional_reconstruction/emergency_complete_regulatory_capture)."""

EPISTEMIC_INSTITUTIONAL_REGULATORY_CAPTURE_PROMPT = """Detect epistemic institutional regulatory capture:

Regulatory behavior: {regulatory_behavior}
Revolving door pattern: {revolving_door_pattern}
Industry framing adoption: {industry_framing_adoption}
Public interest displacement: {public_interest_displacement}
Domain: {domain}
Context: {context}

Are regulators serving regulated industry interests? Return ONLY valid JSON."""


class EpistemicInstitutionalRegulatoryCaptureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        regulatory_behavior: str,
        *,
        revolving_door_pattern: str = "",
        industry_framing_adoption: str = "",
        public_interest_displacement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_REGULATORY_CAPTURE_PROMPT.format(
                regulatory_behavior=regulatory_behavior,
                revolving_door_pattern=revolving_door_pattern or "Not specified",
                industry_framing_adoption=industry_framing_adoption or "Not specified",
                public_interest_displacement=public_interest_displacement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_REGULATORY_CAPTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "regulatory_behavior": regulatory_behavior[:200],
            "regulatory_capture_detected": data.get("regulatory_capture_detected", False),
            "severity": data.get("severity", ""),
            "revolving_door_pattern": data.get("revolving_door_pattern", ""),
            "industry_framing_adoption": data.get("industry_framing_adoption", ""),
            "public_interest_displacement": data.get("public_interest_displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
