"""EpistemicInstitutionalKnowledgeMonopolyService - Knowledge Monopoly Detection.

Detects knowledge monopoly where institutions control access to information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_KNOWLEDGE_MONOPOLY_SYSTEM = """You are an epistemic institutional knowledge monopoly specialist. Given information access patterns, assess whether institutions control access to knowledge:

Key concepts:
- Knowledge monopoly: institutional control over who can access or produce knowledge
- Access restriction: limiting information availability to maintain power
- Production control: determining what counts as legitimate knowledge
- Dissemination gatekeeping: controlling how knowledge spreads

When knowledge monopoly IS present:
- Access artificially restricted
- Production controlled by few
- Dissemination gatekept
- Alternative sources delegitimized
- Power maintained through information control

When no knowledge monopoly:
- Access appropriately managed
- Production open to qualified contributors
- Dissemination serves public interest
- Multiple sources recognized
- Restrictions serve legitimate purposes

Output JSON with: knowledge_monopoly_detected (bool), severity (none/mild/moderate/severe), access_restriction (what access restricted), production_control (what production controlled), dissemination_gatekeeping (what dissemination gatekept), recommendation (no_knowledge_monopoly/mild_access_check/significant_openness_needed/major_access_reconstruction/emergency_complete_knowledge_monopoly)."""

EPISTEMIC_INSTITUTIONAL_KNOWLEDGE_MONOPOLY_PROMPT = """Detect epistemic institutional knowledge monopoly:

Information access: {information_access}
Access restriction: {access_restriction}
Production control: {production_control}
Dissemination gatekeeping: {dissemination_gatekeeping}
Domain: {domain}
Context: {context}

Are institutions controlling access to knowledge? Return ONLY valid JSON."""


class EpistemicInstitutionalKnowledgeMonopolyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_access: str,
        *,
        access_restriction: str = "",
        production_control: str = "",
        dissemination_gatekeeping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_KNOWLEDGE_MONOPOLY_PROMPT.format(
                information_access=information_access,
                access_restriction=access_restriction or "Not specified",
                production_control=production_control or "Not specified",
                dissemination_gatekeeping=dissemination_gatekeeping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_KNOWLEDGE_MONOPOLY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_access": information_access[:200],
            "knowledge_monopoly_detected": data.get("knowledge_monopoly_detected", False),
            "severity": data.get("severity", ""),
            "access_restriction": data.get("access_restriction", ""),
            "production_control": data.get("production_control", ""),
            "dissemination_gatekeeping": data.get("dissemination_gatekeeping", ""),
            "recommendation": data.get("recommendation", ""),
        }
