"""EpistemicOrthorexiaService — Epistemic Orthorexia Detection.

Detects epistemic orthorexia — obsessive pursuit of intellectually
'pure' or 'clean' knowledge, rejecting anything deemed impure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ORTHOREXIA_SYSTEM = """You are an epistemic orthorexia specialist. Given obsessive pursuit of pure knowledge, assess orthorexia patterns:

Key concepts:
- Epistemic orthorexia: obsessive pursuit of intellectually pure knowledge
- Purity obsession: only accepting pristine, verified information
- Source hierarchy: rigid ranking of acceptable knowledge sources
- Contamination fear: avoiding any potentially impure information
- Moral superiority: feeling virtuous about knowledge purity
- Social isolation: rejecting others with impure knowledge
- Nutritional deficiency: missing important knowledge from rejected sources

When epistemic orthorexia IS present:
- Obsessive pursuit of pure knowledge
- Only accepting pristine information
- Rigid source hierarchy
- Avoiding potentially impure information
- Feeling virtuous about purity
- Rejecting others with impure knowledge
- Missing important knowledge

When no orthorexia:
- Flexible knowledge intake
- Accepting imperfect sources
- Pragmatic source evaluation
- Comfortable with uncertainty
- No moral superiority
- Inclusive of diverse sources
- Comprehensive knowledge base

Output JSON with: orthorexia_detected (bool), severity (none/mild/moderate/severe), purity_obsession (what standards), source_rigidity (what hierarchy), contamination_fear (what avoidance), moral_superiority (what virtue signaling), recommendation (no_orthorexia/mild_flexibility_training/significant_exposure_therapy/major_intensive_program/emergency_severe_restriction)."""

EPISTEMIC_ORTHOREXIA_PROMPT = """Detect epistemic orthorexia:

Purity obsession: {purity_obsession}
Source rigidity: {source_rigidity}
Contamination fear: {contamination_fear}
Moral superiority: {moral_superiority}
Domain: {domain}
Context: {context}

Is there obsessive pursuit of intellectually pure knowledge rejecting impure sources? Return ONLY valid JSON."""


class EpistemicOrthorexiaService:
    """Detects epistemic orthorexia — obsessive pursuit of pure knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        purity_obsession: str,
        *,
        source_rigidity: str = "",
        contamination_fear: str = "",
        moral_superiority: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic orthorexia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ORTHOREXIA_PROMPT.format(
                purity_obsession=purity_obsession,
                source_rigidity=source_rigidity or "Not specified",
                contamination_fear=contamination_fear or "Not specified",
                moral_superiority=moral_superiority or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ORTHOREXIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "purity_obsession": purity_obsession[:200],
            "orthorexia_detected": data.get("orthorexia_detected", False),
            "severity": data.get("severity", ""),
            "source_rigidity": data.get("source_rigidity", ""),
            "contamination_fear": data.get("contamination_fear", ""),
            "moral_superiority": data.get("moral_superiority", ""),
            "recommendation": data.get("recommendation", ""),
        }
