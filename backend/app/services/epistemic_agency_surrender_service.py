"""EpistemicAgencySurrenderService — Epistemic Agency Surrender Detection.

Detects epistemic agency surrender — surrendering intellectual agency
to authorities or systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AGENCY_SURRENDER_SYSTEM = """You are an epistemic agency surrender specialist. Given surrendering intellectual agency, assess agency surrender:

Key concepts:
- Epistemic agency surrender: surrendering intellectual agency to authorities
- Authority deference: letting others think for you
- System submission: accepting system outputs without question
- Intellectual abdication: giving up responsibility for own beliefs
- Expert worship: treating expert opinion as unquestionable
- Algorithmic submission: letting algorithms decide what to believe
- Institutional capture: letting institutions determine one's views

When epistemic agency surrender IS present:
- Surrendering agency to authorities
- Letting others think for you
- Accepting without question
- Giving up belief responsibility
- Treating expert as unquestionable
- Letting algorithms decide
- Institutions determining views

When no agency surrender:
- Maintaining agency
- Thinking for oneself
- Questioning appropriately
- Owning beliefs
- Critical of experts
- Evaluating algorithmic output
- Independent of institutions

Output JSON with: agency_surrender_detected (bool), severity (none/mild/moderate/severe), authority_deference (what letting others think about), system_submission (what accepting without question), intellectual_abdication (what giving up responsibility for), algorithmic_submission (what letting algorithms decide), recommendation (no_agency_surrender/mild_independence_practice/significant_agency_recovery/major_intensive_sovereignty_work/emergency_complete_intellectual_abdication)."""

EPISTEMIC_AGENCY_SURRENDER_PROMPT = """Detect epistemic agency surrender:

Authority deference: {authority_deference}
System submission: {system_submission}
Intellectual abdication: {intellectual_abdication}
Algorithmic submission: {algorithmic_submission}
Domain: {domain}
Context: {context}

Is there surrendering intellectual agency to authorities or systems? Return ONLY valid JSON."""


class EpistemicAgencySurrenderService:
    """Detects epistemic agency surrender — surrendering intellectual agency."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        authority_deference: str,
        *,
        system_submission: str = "",
        intellectual_abdication: str = "",
        algorithmic_submission: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic agency surrender."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AGENCY_SURRENDER_PROMPT.format(
                authority_deference=authority_deference,
                system_submission=system_submission or "Not specified",
                intellectual_abdication=intellectual_abdication or "Not specified",
                algorithmic_submission=algorithmic_submission or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AGENCY_SURRENDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authority_deference": authority_deference[:200],
            "agency_surrender_detected": data.get("agency_surrender_detected", False),
            "severity": data.get("severity", ""),
            "system_submission": data.get("system_submission", ""),
            "intellectual_abdication": data.get("intellectual_abdication", ""),
            "algorithmic_submission": data.get("algorithmic_submission", ""),
            "recommendation": data.get("recommendation", ""),
        }
