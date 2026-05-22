"""IrreducibilityBlindnessService — Irreducibility Blindness Detection.

Detects irreducibility blindness — failing to recognize genuinely
irreducible complexity, insisting that all phenomena can be decomposed
into simpler parts without loss of essential properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IRREDUCIBILITY_BLINDNESS_SYSTEM = """You are an irreducibility blindness specialist. Given an analysis, assess whether genuinely irreducible complexity is being missed:

Key concepts:
- Irreducibility blindness: failing to see genuine irreducibility
- Forced decomposition: breaking apart what cannot be separated
- Holism denial: refusing to acknowledge wholes greater than parts
- Gestalt blindness: missing properties that exist only in wholes
- Synergy denial: ignoring genuine synergistic effects
- Composition fallacy: assuming whole equals sum of parts
- Reductive overreach: reducing beyond what's valid

When irreducibility blindness IS present:
- Genuinely irreducible phenomena forced into parts
- Holistic properties denied or dismissed
- Gestalt effects ignored in analysis
- Synergistic interactions treated as additive
- Wholes assumed equal to sum of parts
- Reduction attempted beyond valid limits
- Essential properties lost in decomposition

When reduction is appropriate:
- Decomposition preserves essential properties
- Holistic effects accounted for after reduction
- Gestalt properties recognized where present
- Synergies measured and included
- Composition effects acknowledged
- Reduction bounded by validity
- Lost properties noted and addressed

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), analysis (what analysis is performed), irreducible (what is genuinely irreducible), forced_reduction (what reduction is forced), lost_properties (what is lost in reduction), recommendation (appropriate_reduction/mild_reductive_overreach/significant_irreducibility_blindness/major_forced_decomposition/recognize_genuine_irreducibility)."""

IRREDUCIBILITY_BLINDNESS_PROMPT = """Detect irreducibility blindness:

Analysis: {analysis}
Phenomenon: {phenomenon}
Decomposition: {decomposition}
Lost properties: {lost}
Domain: {domain}
Context: {context}

Is genuinely irreducible complexity being missed or forced into parts? Return ONLY valid JSON."""


class IrreducibilityBlindnessService:
    """Detects irreducibility blindness — missing genuine irreducibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        phenomenon: str = "",
        decomposition: str = "",
        lost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect irreducibility blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IRREDUCIBILITY_BLINDNESS_PROMPT.format(
                analysis=analysis,
                phenomenon=phenomenon or "Not specified",
                decomposition=decomposition or "Not specified",
                lost=lost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IRREDUCIBILITY_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "irreducible": data.get("irreducible", ""),
            "forced_reduction": data.get("forced_reduction", ""),
            "lost_properties": data.get("lost_properties", ""),
            "recommendation": data.get("recommendation", ""),
        }
