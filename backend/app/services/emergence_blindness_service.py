"""EmergenceBlindnessService — Emergence Blindness Detection.

Detects emergence blindness — the failure to recognize emergent
properties that arise from system interactions but cannot be
predicted from individual components alone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EMERGENCE_BLINDNESS_SYSTEM = """You are an emergence blindness specialist. Given an analysis, assess whether emergent properties are being missed:

Key concepts:
- Emergence: system-level properties not predictable from components
- Downward causation: system-level patterns constraining components
- Nonlinear interactions: components interacting in unexpected ways
- Phase transitions: qualitative changes at critical thresholds
- Self-organization: order arising without central control
- Synergy: whole greater than sum of parts
- Reductionism limits: when breaking down loses essential properties

When emergence blindness IS present:
- System analyzed only through its components
- Interaction effects ignored or dismissed
- "Sum of parts" thinking applied to complex systems
- Phase transitions or tipping points not considered
- Self-organizing behavior not recognized
- Emergent properties attributed to individual components
- System-level patterns invisible in component-level analysis

When emergence is recognized:
- System-level properties explicitly identified
- Interactions between components analyzed
- Nonlinear effects and thresholds considered
- Self-organization recognized where present
- Emergent properties not reduced to components
- Both component and system levels analyzed
- Phase transitions and tipping points identified

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), system (what system is being analyzed), emergent_properties (what system-level properties are missed), interactions (what component interactions matter), reductionism (how analysis reduces to components), recommendation (emergence_recognized/mild_blindness/significant_reductionism/major_emergence_missed/analyze_at_system_level)."""

EMERGENCE_BLINDNESS_PROMPT = """Detect emergence blindness:

Analysis: {analysis}
System: {system}
Components: {components}
Interactions: {interactions}
Domain: {domain}
Context: {context}

Are emergent system-level properties being missed? Return ONLY valid JSON."""


class EmergenceBlindnessService:
    """Detects emergence blindness — missing system-level properties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        system: str = "",
        components: str = "",
        interactions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect emergence blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EMERGENCE_BLINDNESS_PROMPT.format(
                analysis=analysis,
                system=system or "Not specified",
                components=components or "Not specified",
                interactions=interactions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EMERGENCE_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "emergent_properties": data.get("emergent_properties", ""),
            "interactions": data.get("interactions", ""),
            "reductionism": data.get("reductionism", ""),
            "recommendation": data.get("recommendation", ""),
        }
