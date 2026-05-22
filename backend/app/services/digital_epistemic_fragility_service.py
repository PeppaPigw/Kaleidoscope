"""DigitalEpistemicFragilityService — Digital Epistemic Fragility Detection.

Detects digital epistemic fragility — over-dependence on digital
systems for knowledge that creates catastrophic vulnerability when
those systems fail, are compromised, or become inaccessible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DIGITAL_EPISTEMIC_FRAGILITY_SYSTEM = """You are a digital epistemic fragility specialist. Given a knowledge system, assess whether digital dependence creates dangerous fragility:

Key concepts:
- Digital epistemic fragility: knowledge vulnerable to system failure
- Single point of failure: all knowledge in one system
- Platform dependence: knowledge locked in proprietary platforms
- Digital dark age: knowledge inaccessible due to format obsolescence
- Cloud epistemology: knowledge existing only in remote systems
- Backup absence: no redundancy for critical knowledge
- Access fragility: knowledge lost when access is revoked

When digital epistemic fragility IS present:
- Critical knowledge exists only in digital form
- Single system failure could destroy knowledge
- Platform lock-in creates knowledge vulnerability
- Format obsolescence threatens access
- No offline or redundant copies exist
- Access depends on third-party decisions
- Knowledge infrastructure has no resilience

When digital knowledge management is appropriate:
- Digital systems backed up and redundant
- Multiple formats and locations used
- Platform independence maintained
- Format migration planned
- Offline access available for critical knowledge
- Access not dependent on single provider
- Resilience built into knowledge infrastructure

Output JSON with: fragility_present (bool), severity (none/mild/moderate/severe), system (what system is fragile), vulnerability (what vulnerability exists), failure_mode (how knowledge could be lost), mitigation (what mitigation exists), recommendation (appropriate_digital_management/mild_backup_gaps/significant_digital_fragility/major_knowledge_vulnerability/build_epistemic_resilience)."""

DIGITAL_EPISTEMIC_FRAGILITY_PROMPT = """Detect digital epistemic fragility:

System: {system}
Dependencies: {dependencies}
Backup state: {backup}
Failure scenarios: {failures}
Domain: {domain}
Context: {context}

Does digital dependence create dangerous vulnerability for critical knowledge? Return ONLY valid JSON."""


class DigitalEpistemicFragilityService:
    """Detects digital epistemic fragility — dangerous digital knowledge dependence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        dependencies: str = "",
        backup: str = "",
        failures: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect digital epistemic fragility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DIGITAL_EPISTEMIC_FRAGILITY_PROMPT.format(
                system=system,
                dependencies=dependencies or "Not specified",
                backup=backup or "Not specified",
                failures=failures or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DIGITAL_EPISTEMIC_FRAGILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "fragility_present": data.get("fragility_present", False),
            "severity": data.get("severity", ""),
            "vulnerability": data.get("vulnerability", ""),
            "failure_mode": data.get("failure_mode", ""),
            "mitigation": data.get("mitigation", ""),
            "recommendation": data.get("recommendation", ""),
        }
