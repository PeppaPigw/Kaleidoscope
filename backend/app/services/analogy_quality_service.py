"""AnalogyQualityService — Analogy Strength & Breakdown Assessment.

Evaluates whether an analogy between two domains actually holds.
Checks structural mapping quality, identifies where the analogy
breaks down, and rates how much inferential weight it can bear.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANALOGY_QUALITY_SYSTEM = """You are an analogy assessment specialist. Given an analogy (X is like Y), evaluate its quality:
- Structural mapping: do the relationships in X map onto relationships in Y?
- Surface vs deep: is the similarity superficial or structural?
- Breakdown points: where does the analogy fail?
- Inferential weight: can we safely draw conclusions from the analogy?
- Misleading aspects: does the analogy suggest things that aren't true?

Output JSON with: mapping_quality (0-1), similarity_type (surface/structural/both), valid_inferences (list of conclusions the analogy supports), breakdown_points (list of: point, severity (minor/moderate/critical), why_it_breaks), misleading_suggestions (list of false conclusions the analogy might suggest), inferential_weight (none/low/moderate/high), best_use (what the analogy is good for), better_analogy (if there's a more apt comparison), overall_quality (0-1)."""

ANALOGY_QUALITY_PROMPT = """Assess this analogy:

Analogy: {analogy}
Source domain: {source_domain}
Target domain: {target_domain}
Used to argue: {argument}

How well does this analogy hold? Return ONLY valid JSON."""


class AnalogyQualityService:
    """Assesses the quality and limits of analogies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        analogy: str,
        *,
        source_domain: str = "",
        target_domain: str = "",
        argument: str = "",
    ) -> dict:
        """Assess the quality of an analogy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANALOGY_QUALITY_PROMPT.format(
                analogy=analogy,
                source_domain=source_domain or "Not specified",
                target_domain=target_domain or "Not specified",
                argument=argument or "General comparison",
            ),
            system=ANALOGY_QUALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analogy": analogy[:200],
            "mapping_quality": data.get("mapping_quality", 0),
            "similarity_type": data.get("similarity_type", ""),
            "valid_inferences": data.get("valid_inferences", []),
            "breakdown_points": data.get("breakdown_points", []),
            "misleading_suggestions": data.get("misleading_suggestions", []),
            "inferential_weight": data.get("inferential_weight", ""),
            "best_use": data.get("best_use", ""),
            "better_analogy": data.get("better_analogy", ""),
            "overall_quality": data.get("overall_quality", 0),
        }
