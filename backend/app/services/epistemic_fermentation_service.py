"""EpistemicFermentationService — Epistemic Fermentation Detection.

Detects epistemic fermentation — ideas transforming through
uncontrolled processes, producing both useful and toxic byproducts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FERMENTATION_SYSTEM = """You are an epistemic fermentation specialist. Given an idea transformation pattern, assess whether uncontrolled processes produce toxic byproducts:

Key concepts:
- Epistemic fermentation: ideas transforming through uncontrolled processes
- Uncontrolled transformation: ideas changing without guidance
- Toxic byproduct: harmful ideas produced as side effects
- Useful product: valuable insights produced alongside toxins
- Culture contamination: wrong intellectual cultures driving transformation
- Spoilage: ideas going bad through wrong fermentation
- Controlled vs wild: difference between guided and unguided transformation

When epistemic fermentation IS present:
- Ideas transforming through uncontrolled processes
- Ideas changing without intellectual guidance
- Harmful ideas produced as side effects of transformation
- Valuable insights mixed with toxic byproducts
- Wrong intellectual cultures driving the transformation
- Ideas going bad through unguided processes
- Transformation happening without quality control

When controlled transformation is present:
- Ideas transforming through guided processes
- Intellectual guidance directing transformation
- No harmful byproducts from transformation
- Valuable insights produced cleanly
- Appropriate intellectual cultures guiding transformation
- Ideas improving through guided processes
- Quality control maintained throughout

Output JSON with: fermentation_present (bool), severity (none/mild/moderate/severe), ideas (what ideas are fermenting), process (what uncontrolled process), toxic_byproduct (what toxic byproducts), contamination (what culture contamination), recommendation (controlled_transformation/mild_fermentation/significant_uncontrolled/major_toxic_production/guide_the_process)."""

EPISTEMIC_FERMENTATION_PROMPT = """Detect epistemic fermentation:

Ideas: {ideas}
Process: {process}
Toxic byproduct: {toxic_byproduct}
Contamination: {contamination}
Domain: {domain}
Context: {context}

Are ideas transforming through uncontrolled processes producing toxic byproducts? Return ONLY valid JSON."""


class EpistemicFermentationService:
    """Detects epistemic fermentation — uncontrolled idea transformation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        process: str = "",
        toxic_byproduct: str = "",
        contamination: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fermentation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FERMENTATION_PROMPT.format(
                ideas=ideas,
                process=process or "Not specified",
                toxic_byproduct=toxic_byproduct or "Not specified",
                contamination=contamination or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FERMENTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "fermentation_present": data.get("fermentation_present", False),
            "severity": data.get("severity", ""),
            "process": data.get("process", ""),
            "toxic_byproduct": data.get("toxic_byproduct", ""),
            "contamination": data.get("contamination", ""),
            "recommendation": data.get("recommendation", ""),
        }
