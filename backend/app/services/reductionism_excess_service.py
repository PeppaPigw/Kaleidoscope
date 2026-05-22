"""ReductionismExcessService — Reductionism Excess Detection.

Detects excessive reductionism — when breaking complex systems
into parts loses essential system-level properties that only
exist at the level of the whole.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REDUCTIONISM_EXCESS_SYSTEM = """You are a reductionism excess specialist. Given an analysis, assess whether reductionism is losing essential properties:

Key concepts:
- Excessive reductionism: decomposition losing essential properties
- Holism: some properties only exist at the system level
- Context dependence: parts behave differently in isolation vs in system
- Relational properties: properties that exist between, not within, components
- Mereological fallacy: attributing system properties to parts
- Composition effects: how parts combine matters, not just what they are
- Appropriate level of analysis: matching analysis level to phenomenon

When reductionism IS excessive:
- Essential properties lost when system decomposed
- Parts analyzed in isolation when context matters
- Relational properties attributed to individual components
- System behavior predicted from parts alone when interactions dominate
- Appropriate level of analysis is system, but analysis is at component level
- Context-dependent behavior analyzed context-free
- Composition effects ignored

When reductionism is appropriate:
- Decomposition preserves essential properties
- Parts can be meaningfully analyzed in isolation
- System behavior predictable from component behavior
- Interactions are weak relative to component properties
- Analysis level matches the phenomenon
- Context effects are minimal
- Composition is simple (additive, not synergistic)

Output JSON with: excess_present (bool), severity (none/mild/moderate/severe), system (what is being reduced), lost_properties (what is lost in reduction), appropriate_level (what level should be analyzed), decomposition (how the system is being broken down), recommendation (appropriate_reduction/mild_excess/significant_loss/major_mereological_error/analyze_at_system_level)."""

REDUCTIONISM_EXCESS_PROMPT = """Detect excessive reductionism:

Analysis: {analysis}
System: {system}
Decomposition: {decomposition}
Properties claimed: {properties}
Domain: {domain}
Context: {context}

Is reductionism losing essential system-level properties? Return ONLY valid JSON."""


class ReductionismExcessService:
    """Detects excessive reductionism — decomposition losing essential properties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        system: str = "",
        decomposition: str = "",
        properties: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect excessive reductionism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REDUCTIONISM_EXCESS_PROMPT.format(
                analysis=analysis,
                system=system or "Not specified",
                decomposition=decomposition or "Not specified",
                properties=properties or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REDUCTIONISM_EXCESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "excess_present": data.get("excess_present", False),
            "severity": data.get("severity", ""),
            "lost_properties": data.get("lost_properties", ""),
            "appropriate_level": data.get("appropriate_level", ""),
            "decomposition": data.get("decomposition", ""),
            "recommendation": data.get("recommendation", ""),
        }
