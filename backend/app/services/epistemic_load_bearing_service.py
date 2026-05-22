"""EpistemicLoadBearingService — Epistemic Load-Bearing Detection.

Detects epistemic load-bearing elements — beliefs whose removal
would collapse the entire knowledge structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LOAD_BEARING_SYSTEM = """You are an epistemic load-bearing specialist. Given a belief system, identify which beliefs are load-bearing — whose removal would collapse the structure:

Key concepts:
- Epistemic load-bearing: beliefs supporting entire structure
- Structural dependency: many beliefs depending on one
- Collapse risk: risk of structural collapse if removed
- Single point of failure: one belief holding up many
- Hidden load: load-bearing status not recognized
- Redundancy absence: no backup if load-bearing belief fails
- Structural vulnerability: vulnerability from concentration

When epistemic load-bearing risk IS present:
- Key beliefs supporting entire knowledge structure
- Many beliefs depending on single foundational belief
- Risk of structural collapse if key belief removed
- Single point of failure in belief system
- Load-bearing status not recognized or acknowledged
- No redundancy if load-bearing belief fails
- Concentrated vulnerability in knowledge structure

When distributed support is present:
- Support distributed across multiple beliefs
- No single belief bearing disproportionate load
- Structure resilient to removal of any single belief
- Multiple points of support
- Load-bearing elements recognized and reinforced
- Redundancy built into structure
- Vulnerability distributed and managed

Output JSON with: load_bearing_present (bool), severity (none/mild/moderate/severe), system (what belief system), load_bearer (what belief is load-bearing), dependents (what depends on it), collapse_risk (what collapse risk exists), recommendation (distributed_support/mild_concentration/significant_load_bearing/major_single_point_failure/build_redundancy)."""

EPISTEMIC_LOAD_BEARING_PROMPT = """Detect epistemic load-bearing:

System: {system}
Load bearer: {load_bearer}
Dependents: {dependents}
Collapse risk: {collapse_risk}
Domain: {domain}
Context: {context}

Are there beliefs whose removal would collapse the entire structure? Return ONLY valid JSON."""


class EpistemicLoadBearingService:
    """Detects epistemic load-bearing elements — beliefs supporting entire structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        load_bearer: str = "",
        dependents: str = "",
        collapse_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic load-bearing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LOAD_BEARING_PROMPT.format(
                system=system,
                load_bearer=load_bearer or "Not specified",
                dependents=dependents or "Not specified",
                collapse_risk=collapse_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LOAD_BEARING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "load_bearing_present": data.get("load_bearing_present", False),
            "severity": data.get("severity", ""),
            "load_bearer": data.get("load_bearer", ""),
            "dependents": data.get("dependents", ""),
            "collapse_risk": data.get("collapse_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
