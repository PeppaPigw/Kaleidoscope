"""EpistemicGatekeepingDeeperService — Epistemic Gatekeeping Deeper Detection.

Detects deeper epistemic gatekeeping — controlling who gets to participate
in knowledge creation and intellectual discourse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GATEKEEPING_DEEPER_SYSTEM = """You are an epistemic gatekeeping specialist. Given controlling participation in knowledge, assess deeper gatekeeping:

Key concepts:
- Epistemic gatekeeping deeper: controlling who participates in knowledge
- Access restriction: restricting access to intellectual discourse
- Credential gatekeeping: requiring credentials to participate
- Language gatekeeping: using language to exclude
- Network gatekeeping: using networks to control access
- Publication gatekeeping: controlling what gets published
- Legitimacy gatekeeping: controlling what counts as legitimate knowledge

When epistemic gatekeeping deeper IS present:
- Controlling who participates
- Restricting access to discourse
- Requiring credentials to participate
- Using language to exclude
- Using networks to control
- Controlling publication
- Controlling legitimacy

When no deeper gatekeeping:
- Open participation
- Accessible discourse
- Merit-based participation
- Inclusive language
- Open networks
- Fair publication
- Inclusive legitimacy

Output JSON with: gatekeeping_deeper_detected (bool), severity (none/mild/moderate/severe), access_restriction (what access restricted), credential_gatekeeping (what credentials required), language_gatekeeping (what language used to exclude), legitimacy_gatekeeping (what legitimacy controlled), recommendation (no_gatekeeping/mild_openness_practice/significant_access_expansion/major_intensive_democratization/emergency_complete_knowledge_control)."""

EPISTEMIC_GATEKEEPING_DEEPER_PROMPT = """Detect deeper epistemic gatekeeping:

Access restriction: {access_restriction}
Credential gatekeeping: {credential_gatekeeping}
Language gatekeeping: {language_gatekeeping}
Legitimacy gatekeeping: {legitimacy_gatekeeping}
Domain: {domain}
Context: {context}

Is there controlling who gets to participate in knowledge? Return ONLY valid JSON."""


class EpistemicGatekeepingDeeperService:
    """Detects deeper epistemic gatekeeping — controlling participation in knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        access_restriction: str,
        *,
        credential_gatekeeping: str = "",
        language_gatekeeping: str = "",
        legitimacy_gatekeeping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deeper epistemic gatekeeping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GATEKEEPING_DEEPER_PROMPT.format(
                access_restriction=access_restriction,
                credential_gatekeeping=credential_gatekeeping or "Not specified",
                language_gatekeeping=language_gatekeeping or "Not specified",
                legitimacy_gatekeeping=legitimacy_gatekeeping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GATEKEEPING_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "access_restriction": access_restriction[:200],
            "gatekeeping_deeper_detected": data.get("gatekeeping_deeper_detected", False),
            "severity": data.get("severity", ""),
            "credential_gatekeeping": data.get("credential_gatekeeping", ""),
            "language_gatekeeping": data.get("language_gatekeeping", ""),
            "legitimacy_gatekeeping": data.get("legitimacy_gatekeeping", ""),
            "recommendation": data.get("recommendation", ""),
        }
