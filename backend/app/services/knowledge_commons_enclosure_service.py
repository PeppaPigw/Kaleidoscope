"""KnowledgeCommonsEnclosureService — Knowledge Commons Enclosure Detection.

Detects knowledge commons enclosure — the privatization or
restriction of knowledge that was previously shared, reducing
collective epistemic capacity for private gain.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_COMMONS_ENCLOSURE_SYSTEM = """You are a knowledge commons enclosure specialist. Given a knowledge access situation, assess whether commons are being enclosed:

Key concepts:
- Knowledge commons enclosure: privatizing shared knowledge
- Intellectual enclosure: restricting previously open knowledge
- Paywall creep: expanding barriers to knowledge access
- Patent thickets: using IP to block knowledge use
- Data enclosure: privatizing collectively generated data
- Access restriction: limiting who can use knowledge
- Epistemic rent-seeking: extracting value from knowledge access

When knowledge commons enclosure IS present:
- Previously shared knowledge being privatized
- Access barriers erected where none existed
- Collective knowledge appropriated for private gain
- IP used to restrict rather than incentivize
- Data generated collectively but owned privately
- Knowledge access becoming more restricted over time
- Epistemic rent-seeking extracting value from access

When knowledge protection is appropriate:
- Protection incentivizes knowledge creation
- Access restrictions temporary and justified
- Public interest balanced with private rights
- Knowledge eventually enters commons
- Protection serves innovation
- Access maintained for research and education
- Restrictions proportional to investment

Output JSON with: enclosure_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is enclosed), mechanism (how enclosure works), previous_access (what access existed before), beneficiary (who benefits from enclosure), recommendation (appropriate_knowledge_protection/mild_access_restriction/significant_commons_enclosure/major_knowledge_privatization/restore_knowledge_commons)."""

KNOWLEDGE_COMMONS_ENCLOSURE_PROMPT = """Detect knowledge commons enclosure:

Knowledge at issue: {knowledge}
Access change: {access}
Mechanism: {mechanism}
Previous state: {previous}
Domain: {domain}
Context: {context}

Is previously shared knowledge being privatized or restricted? Return ONLY valid JSON."""


class KnowledgeCommonsEnclosureService:
    """Detects knowledge commons enclosure — privatizing shared knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        access: str = "",
        mechanism: str = "",
        previous: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge commons enclosure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_COMMONS_ENCLOSURE_PROMPT.format(
                knowledge=knowledge,
                access=access or "Not specified",
                mechanism=mechanism or "Not specified",
                previous=previous or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_COMMONS_ENCLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "enclosure_present": data.get("enclosure_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "previous_access": data.get("previous_access", ""),
            "beneficiary": data.get("beneficiary", ""),
            "recommendation": data.get("recommendation", ""),
        }
