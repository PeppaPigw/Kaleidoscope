"""EpistemicAnalogySurfaceSimilarityService — Epistemic Analogy Surface Similarity Detection.

Detects epistemic analogy surface similarity — analogies based on superficial
features rather than deep structural relationships between domains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_SURFACE_SIMILARITY_SYSTEM = """You are an epistemic analogy surface similarity specialist. Given surface-level analogies, assess structural validity:

Key concepts:
- Epistemic surface similarity: analogies based on appearance not structure
- Feature matching: matching superficial features while ignoring mechanisms
- Structural mismatch: analogized domains having different causal structures
- Appearance over mechanism: visual or verbal similarity substituting for functional
- Category confusion: surface similarity creating false category membership
- Misleading resemblance: coincidental similarity driving false inference
- Depth neglect: failing to check whether analogy holds at deeper levels

When epistemic surface similarity IS present:
- Analogies based on appearance
- Superficial features matched
- Causal structures differ
- Visual similarity substituting for functional
- False categories created
- Coincidental similarity driving inference
- Deeper levels unchecked

When no surface similarity bias:
- Analogies based on structure
- Deep features matched
- Causal structures aligned
- Functional similarity verified
- Categories well-motivated
- Similarity structurally grounded
- Multiple levels checked

Output JSON with: surface_similarity_detected (bool), severity (none/mild/moderate/severe), feature_matching (what superficial features matched), structural_mismatch (what structures differ), appearance_over_mechanism (what appearance substituting), depth_neglect (what deeper levels unchecked), recommendation (no_surface_similarity/mild_structural_checking/significant_mechanism_verification/major_intensive_structural_analysis/emergency_complete_surface_similarity)."""

EPISTEMIC_ANALOGY_SURFACE_SIMILARITY_PROMPT = """Detect epistemic analogy surface similarity:

Feature matching: {feature_matching}
Structural mismatch: {structural_mismatch}
Appearance over mechanism: {appearance_over_mechanism}
Depth neglect: {depth_neglect}
Domain: {domain}
Context: {context}

Are analogies based on surface features rather than structural relationships? Return ONLY valid JSON."""


class EpistemicAnalogySurfaceSimilarityService:
    """Detects epistemic analogy surface similarity — appearance over structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        feature_matching: str,
        *,
        structural_mismatch: str = "",
        appearance_over_mechanism: str = "",
        depth_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy surface similarity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_SURFACE_SIMILARITY_PROMPT.format(
                feature_matching=feature_matching,
                structural_mismatch=structural_mismatch or "Not specified",
                appearance_over_mechanism=appearance_over_mechanism or "Not specified",
                depth_neglect=depth_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_SURFACE_SIMILARITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "feature_matching": feature_matching[:200],
            "surface_similarity_detected": data.get("surface_similarity_detected", False),
            "severity": data.get("severity", ""),
            "structural_mismatch": data.get("structural_mismatch", ""),
            "appearance_over_mechanism": data.get("appearance_over_mechanism", ""),
            "depth_neglect": data.get("depth_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
