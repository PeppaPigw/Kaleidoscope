"""EpistemicSymbiosisService — Epistemic Symbiosis Detection.

Detects epistemic symbiosis — ideas that can only survive in mutual
dependency, creating fragile pairs vulnerable to collapse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SYMBIOSIS_SYSTEM = """You are an epistemic symbiosis specialist. Given a belief system, assess whether ideas exist in fragile mutual dependency:

Key concepts:
- Epistemic symbiosis: ideas surviving only through mutual dependency
- Fragile pairing: ideas paired so neither can stand alone
- Mutual dependency: each idea requiring the other to survive
- Co-dependent beliefs: beliefs that cannot exist independently
- Collapse vulnerability: if one falls, both fall
- Artificial coupling: coupling not based on logical necessity
- Parasitic symbiosis: one idea benefiting at other's expense

When epistemic symbiosis IS present:
- Ideas surviving only through mutual dependency
- Neither idea can stand alone on its own evidence
- Each idea requiring the other for justification
- Beliefs that cannot exist independently
- If one is disproven, both collapse
- Coupling not based on logical necessity
- One idea potentially parasitic on the other

When legitimate integration is present:
- Ideas connected through genuine logical relationships
- Each idea has independent evidential support
- Connection strengthens but isn't required for survival
- Beliefs can be evaluated independently
- Disproving one doesn't automatically destroy the other
- Coupling reflects genuine logical structure
- Mutual support based on shared evidence

Output JSON with: symbiosis_present (bool), severity (none/mild/moderate/severe), system (what belief system), dependency (what mutual dependency exists), fragility (how fragile the pairing is), collapse_risk (what collapse risk exists), recommendation (legitimate_integration/mild_coupling/significant_symbiosis/major_fragile_dependency/establish_independent_support)."""

EPISTEMIC_SYMBIOSIS_PROMPT = """Detect epistemic symbiosis:

System: {system}
Dependency: {dependency}
Fragility: {fragility}
Collapse risk: {collapse_risk}
Domain: {domain}
Context: {context}

Do ideas exist in fragile mutual dependency where neither can stand alone? Return ONLY valid JSON."""


class EpistemicSymbiosisService:
    """Detects epistemic symbiosis — ideas in fragile mutual dependency."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        dependency: str = "",
        fragility: str = "",
        collapse_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic symbiosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SYMBIOSIS_PROMPT.format(
                system=system,
                dependency=dependency or "Not specified",
                fragility=fragility or "Not specified",
                collapse_risk=collapse_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SYMBIOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "symbiosis_present": data.get("symbiosis_present", False),
            "severity": data.get("severity", ""),
            "dependency": data.get("dependency", ""),
            "fragility": data.get("fragility", ""),
            "collapse_risk": data.get("collapse_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
