"""InstitutionalAmnesiaDetectService — Institutional Amnesia Detection.

Detects institutional amnesia — organizations losing critical knowledge
through turnover, restructuring, or failure to preserve institutional
memory, leading to repeated mistakes and lost capabilities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INSTITUTIONAL_AMNESIA_DETECT_SYSTEM = """You are an institutional amnesia specialist. Given an organizational situation, assess whether critical knowledge is being lost:

Key concepts:
- Institutional amnesia: organization losing critical knowledge
- Knowledge loss through turnover: expertise leaving with people
- Restructuring amnesia: knowledge lost in reorganization
- Repeated mistakes: same errors recurring due to lost memory
- Capability loss: abilities disappearing from organization
- Undocumented knowledge: critical knowledge never recorded
- Memory fragility: institutional memory dependent on few people

When institutional amnesia IS present:
- Critical knowledge being lost through turnover
- Organization repeating past mistakes
- Restructuring destroying knowledge networks
- Capabilities disappearing without replacement
- Key knowledge undocumented and at risk
- Institutional memory fragile and person-dependent
- Lessons learned not preserved or accessible

When knowledge transition is appropriate:
- Knowledge transfer processes in place
- Documentation captures critical knowledge
- Redundancy in knowledge holders
- Lessons learned preserved and accessible
- Restructuring accounts for knowledge preservation
- Institutional memory maintained through systems
- Knowledge loss risks identified and managed

Output JSON with: amnesia_present (bool), severity (none/mild/moderate/severe), organization (what organization is analyzed), knowledge_lost (what knowledge is at risk), mechanism (how loss occurs), consequence (what results from loss), recommendation (appropriate_knowledge_management/mild_documentation_gap/significant_institutional_amnesia/major_capability_loss/preserve_institutional_memory)."""

INSTITUTIONAL_AMNESIA_DETECT_PROMPT = """Detect institutional amnesia:

Organization: {organization}
Knowledge at risk: {knowledge}
Mechanism of loss: {mechanism}
Preservation efforts: {preservation}
Domain: {domain}
Context: {context}

Is the organization losing critical knowledge? Return ONLY valid JSON."""


class InstitutionalAmnesiaDetectService:
    """Detects institutional amnesia — organizations losing critical knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        organization: str,
        *,
        knowledge: str = "",
        mechanism: str = "",
        preservation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect institutional amnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INSTITUTIONAL_AMNESIA_DETECT_PROMPT.format(
                organization=organization,
                knowledge=knowledge or "Not specified",
                mechanism=mechanism or "Not specified",
                preservation=preservation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INSTITUTIONAL_AMNESIA_DETECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "organization": organization[:200],
            "amnesia_present": data.get("amnesia_present", False),
            "severity": data.get("severity", ""),
            "knowledge_lost": data.get("knowledge_lost", ""),
            "mechanism": data.get("mechanism", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
