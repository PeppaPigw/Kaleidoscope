"""EmergentIgnoranceService — Emergent Ignorance Detection.

Detects emergent ignorance — ignorance that arises from the
interaction of individually knowledgeable agents, where no one
is individually ignorant but the system as a whole fails to know.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EMERGENT_IGNORANCE_SYSTEM = """You are an emergent ignorance specialist. Given a complex system, assess whether systemic ignorance emerges from individually knowledgeable parts:

Key concepts:
- Emergent ignorance: system-level ignorance from knowledgeable parts
- Coordination failure: knowledge exists but isn't connected
- Silo blindness: each part knows its piece but not the whole
- Integration failure: knowledge not synthesized across boundaries
- Complexity-induced ignorance: complexity preventing understanding
- Distributed knowledge gaps: gaps between distributed knowledge
- System-level blindness: what no individual can see

When emergent ignorance IS present:
- Individual agents knowledgeable but system ignorant
- Knowledge exists in parts but not synthesized
- Silos prevent whole-system understanding
- Coordination failures create knowledge gaps
- Complexity prevents anyone from seeing the whole
- Distributed knowledge not integrated
- System-level patterns invisible to all parts

When distributed knowledge is appropriate:
- Specialization serves overall understanding
- Integration mechanisms connect knowledge
- Coordination ensures whole-system awareness
- Complexity managed through appropriate abstraction
- Distributed knowledge synthesized regularly
- System-level patterns monitored
- No one needs to know everything

Output JSON with: ignorance_present (bool), severity (none/mild/moderate/severe), system (what system is analyzed), individual_knowledge (what individuals know), system_gap (what system doesn't know), mechanism (how ignorance emerges), recommendation (appropriate_distributed_knowledge/mild_integration_gap/significant_emergent_ignorance/major_system_blindness/integrate_distributed_knowledge)."""

EMERGENT_IGNORANCE_PROMPT = """Detect emergent ignorance:

System: {system}
Individual knowledge: {individual}
System-level gaps: {gaps}
Integration mechanisms: {integration}
Domain: {domain}
Context: {context}

Does system-level ignorance emerge despite individually knowledgeable parts? Return ONLY valid JSON."""


class EmergentIgnoranceService:
    """Detects emergent ignorance — system-level ignorance from knowledgeable parts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        individual: str = "",
        gaps: str = "",
        integration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect emergent ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EMERGENT_IGNORANCE_PROMPT.format(
                system=system,
                individual=individual or "Not specified",
                gaps=gaps or "Not specified",
                integration=integration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EMERGENT_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "ignorance_present": data.get("ignorance_present", False),
            "severity": data.get("severity", ""),
            "individual_knowledge": data.get("individual_knowledge", ""),
            "system_gap": data.get("system_gap", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
