"""CausalOversimplificationService — Causal Oversimplification Detection.

Detects causal oversimplification — reducing complex multicausal
phenomena to single causes, ignoring the web of contributing
factors and their interactions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CAUSAL_OVERSIMPLIFICATION_SYSTEM = """You are a causal oversimplification specialist. Given an explanation, assess whether complex causation is being oversimplified:

Key concepts:
- Monocausal explanation: attributing to single cause what has many
- Causal web: multiple interacting causes
- Necessary vs sufficient: single cause may be necessary but not sufficient
- Proximate vs distal: immediate vs underlying causes
- Overdetermination: multiple sufficient causes
- INUS conditions: insufficient but necessary parts of unnecessary but sufficient conditions
- Causal chains: sequences of causes and effects

When causal oversimplification IS present:
- Single cause cited for multicausal phenomenon
- Proximate cause treated as complete explanation
- Contributing factors ignored or dismissed
- Interactions between causes not considered
- Necessary condition treated as sufficient
- Complex causal web reduced to simple chain
- Structural causes ignored in favor of individual ones

When causal reasoning is appropriately complex:
- Multiple causes identified and weighted
- Interactions between causes considered
- Necessary vs sufficient distinguished
- Proximate and distal causes both addressed
- Structural and individual factors both considered
- Causal uncertainty acknowledged
- Appropriate simplification for context (not all simplification is wrong)

Output JSON with: oversimplification_present (bool), severity (none/mild/moderate/severe), phenomenon (what is being explained), cited_cause (single cause given), missing_causes (what other causes are ignored), interactions (what causal interactions are missed), recommendation (appropriate_complexity/mild_simplification/significant_reduction/major_monocausal_error/map_causal_web)."""

CAUSAL_OVERSIMPLIFICATION_PROMPT = """Detect causal oversimplification:

Explanation: {explanation}
Phenomenon: {phenomenon}
Cited cause: {cited_cause}
Known factors: {known_factors}
Domain: {domain}
Context: {context}

Is complex multicausal reality being oversimplified to a single cause? Return ONLY valid JSON."""


class CausalOversimplificationService:
    """Detects causal oversimplification — reducing multicausal to monocausal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        phenomenon: str = "",
        cited_cause: str = "",
        known_factors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect causal oversimplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CAUSAL_OVERSIMPLIFICATION_PROMPT.format(
                explanation=explanation,
                phenomenon=phenomenon or "Not specified",
                cited_cause=cited_cause or "Not specified",
                known_factors=known_factors or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CAUSAL_OVERSIMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "oversimplification_present": data.get("oversimplification_present", False),
            "severity": data.get("severity", ""),
            "cited_cause": data.get("cited_cause", ""),
            "missing_causes": data.get("missing_causes", ""),
            "interactions": data.get("interactions", ""),
            "recommendation": data.get("recommendation", ""),
        }
