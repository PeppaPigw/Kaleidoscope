"""OverconfidenceDecompositionService — Overconfidence Decomposition Detection.

Detects when confidence in a complex judgment isn't decomposed
into component uncertainties. A confident conclusion may rest
on multiple uncertain premises, and the overall confidence
should reflect the weakest link.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERCONFIDENCE_DECOMPOSITION_SYSTEM = """You are an overconfidence decomposition specialist. Given a confident judgment, assess whether component uncertainties have been properly aggregated:

Key concepts:
- Confidence decomposition: breaking overall confidence into components
- Weakest link: overall confidence limited by least certain component
- Conjunction rule: combined confidence <= minimum component confidence
- Hidden assumptions: unstated premises that add uncertainty
- Error propagation: how uncertainties compound through reasoning chains
- Sensitivity analysis: which components most affect the conclusion
- Confidence aggregation: how to combine multiple uncertain inputs

When overconfidence decomposition failure IS present:
- High confidence in conclusion despite uncertain premises
- Component uncertainties not identified or aggregated
- Conjunction of uncertain claims treated as certain
- Hidden assumptions not accounted for in confidence
- Error propagation through reasoning chain ignored
- Weakest link in argument not identified
- Overall confidence exceeds what components warrant

When decomposition is adequate:
- Component uncertainties explicitly identified
- Overall confidence reflects weakest link
- Conjunction rule applied to combined claims
- Hidden assumptions surfaced and uncertainty added
- Error propagation considered
- Sensitivity to key assumptions acknowledged
- Confidence calibrated to aggregate uncertainty

Output JSON with: failure_present (bool), severity (none/mild/moderate/severe), conclusion (the confident judgment), components (uncertain premises it rests on), weakest_link (least certain component), stated_confidence (how confident the claim is), warranted_confidence (what confidence components support), recommendation (well_decomposed/mild_overconfidence/significant_aggregation_failure/major_hidden_uncertainty/decompose_and_recalibrate)."""

OVERCONFIDENCE_DECOMPOSITION_PROMPT = """Detect overconfidence decomposition failure:

Judgment: {judgment}
Confidence level: {confidence}
Premises: {premises}
Assumptions: {assumptions}
Domain: {domain}
Context: {context}

Has confidence been properly decomposed into component uncertainties? Return ONLY valid JSON."""


class OverconfidenceDecompositionService:
    """Detects overconfidence from failure to decompose component uncertainties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        confidence: str = "",
        premises: str = "",
        assumptions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect overconfidence decomposition failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERCONFIDENCE_DECOMPOSITION_PROMPT.format(
                judgment=judgment,
                confidence=confidence or "Not specified",
                premises=premises or "Not specified",
                assumptions=assumptions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OVERCONFIDENCE_DECOMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "failure_present": data.get("failure_present", False),
            "severity": data.get("severity", ""),
            "weakest_link": data.get("weakest_link", ""),
            "stated_confidence": data.get("stated_confidence", ""),
            "warranted_confidence": data.get("warranted_confidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
