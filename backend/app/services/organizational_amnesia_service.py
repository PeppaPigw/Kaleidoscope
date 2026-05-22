"""OrganizationalAmnesiaService — Organizational Amnesia Detection.

Detects organizational amnesia — when organizations lose critical
knowledge through turnover, restructuring, or failure to maintain
institutional memory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ORGANIZATIONAL_AMNESIA_SYSTEM = """You are an organizational amnesia specialist. Given an organizational situation, assess whether critical knowledge is being lost:

Key concepts:
- Institutional memory: accumulated knowledge of how and why things work
- Knowledge loss: critical information disappearing with departures
- Tacit knowledge: unwritten knowledge held by experienced members
- Lessons unlearned: repeating past mistakes due to lost knowledge
- Documentation debt: critical knowledge never written down
- Restructuring amnesia: reorganization destroying knowledge networks
- Onboarding gaps: new members lacking historical context

When organizational amnesia IS present:
- Critical knowledge lost through turnover
- Past mistakes being repeated
- Tacit knowledge not captured or transferred
- Restructuring destroying knowledge networks
- New members lacking essential historical context
- Documentation inadequate for knowledge preservation
- Institutional memory concentrated in few individuals

When knowledge is preserved:
- Critical knowledge documented and accessible
- Knowledge transfer processes in place
- Lessons learned captured and referenced
- Restructuring preserves knowledge networks
- Onboarding includes historical context
- Tacit knowledge made explicit where possible
- Institutional memory distributed across organization

Output JSON with: amnesia_present (bool), severity (none/mild/moderate/severe), organization (what organization), knowledge_lost (what knowledge is at risk), mechanism (how knowledge is being lost), consequences (what happens when knowledge is lost), recommendation (knowledge_preserved/mild_gaps/significant_amnesia/major_institutional_memory_loss/implement_knowledge_transfer)."""

ORGANIZATIONAL_AMNESIA_PROMPT = """Detect organizational amnesia:

Organization: {organization}
Knowledge at risk: {knowledge}
Turnover: {turnover}
Documentation: {documentation}
Domain: {domain}
Context: {context}

Is critical organizational knowledge being lost? Return ONLY valid JSON."""


class OrganizationalAmnesiaService:
    """Detects organizational amnesia — critical knowledge loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        organization: str,
        *,
        knowledge: str = "",
        turnover: str = "",
        documentation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect organizational amnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ORGANIZATIONAL_AMNESIA_PROMPT.format(
                organization=organization,
                knowledge=knowledge or "Not specified",
                turnover=turnover or "Not specified",
                documentation=documentation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ORGANIZATIONAL_AMNESIA_SYSTEM,
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
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
