"""EpistemicParallaxService — Epistemic Parallax Detection.

Detects epistemic parallax — same evidence appearing different
from different viewpoints, creating false disagreement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARALLAX_SYSTEM = """You are an epistemic parallax specialist. Given a disagreement pattern, assess whether apparent differences are due to viewpoint rather than substance:

Key concepts:
- Epistemic parallax: same evidence appearing different from different viewpoints
- Viewpoint artifact: disagreement caused by position not substance
- Apparent displacement: evidence appearing in different positions from different views
- False disagreement: disagreement that dissolves when viewpoints are reconciled
- Perspective illusion: illusion of difference created by perspective
- Baseline difference: different baselines creating apparent disagreement
- Triangulation need: need to combine viewpoints for accurate picture

When epistemic parallax IS present:
- Same evidence appearing different from different viewpoints
- Disagreement caused by position rather than substance
- Evidence appearing displaced depending on observer position
- Disagreement that would dissolve if viewpoints reconciled
- Illusion of difference created by perspective alone
- Different baselines creating apparent disagreement
- Need to triangulate from multiple viewpoints

When genuine disagreement is present:
- Evidence genuinely different regardless of viewpoint
- Disagreement based on substance not position
- Evidence in same position from all viewpoints
- Disagreement persisting even when viewpoints reconciled
- Real differences not caused by perspective
- Same baseline showing genuine disagreement
- Multiple viewpoints confirming the disagreement

Output JSON with: parallax_present (bool), severity (none/mild/moderate/severe), evidence (what evidence shows parallax), viewpoints (what viewpoints differ), displacement (what apparent displacement), false_disagreement (what false disagreement results), recommendation (genuine_disagreement/mild_parallax/significant_viewpoint_artifact/major_false_disagreement/triangulate_viewpoints)."""

EPISTEMIC_PARALLAX_PROMPT = """Detect epistemic parallax:

Evidence: {evidence}
Viewpoints: {viewpoints}
Displacement: {displacement}
False disagreement: {false_disagreement}
Domain: {domain}
Context: {context}

Is apparent disagreement caused by viewpoint differences rather than substantive differences? Return ONLY valid JSON."""


class EpistemicParallaxService:
    """Detects epistemic parallax — viewpoint-caused false disagreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence: str,
        *,
        viewpoints: str = "",
        displacement: str = "",
        false_disagreement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic parallax."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARALLAX_PROMPT.format(
                evidence=evidence,
                viewpoints=viewpoints or "Not specified",
                displacement=displacement or "Not specified",
                false_disagreement=false_disagreement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARALLAX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence": evidence[:200],
            "parallax_present": data.get("parallax_present", False),
            "severity": data.get("severity", ""),
            "viewpoints": data.get("viewpoints", ""),
            "displacement": data.get("displacement", ""),
            "false_disagreement": data.get("false_disagreement", ""),
            "recommendation": data.get("recommendation", ""),
        }
