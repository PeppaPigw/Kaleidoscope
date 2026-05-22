"""CherryPickingService — Cherry Picking Detection.

Detects cherry picking — selectively presenting data, examples,
or evidence that supports a conclusion while ignoring or
suppressing data that contradicts it. Creates a misleading
impression by showing only part of the picture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHERRY_PICKING_SYSTEM = """You are a cherry picking specialist. Given a claim and its supporting evidence, assess whether data has been selectively presented:

Key concepts:
- Cherry picking: selecting only favorable data points
- Confirmation bias in data: seeking only confirming evidence
- Suppressed evidence: hiding contradicting data
- Representative sampling: is the evidence representative?
- Base rate: what does the full dataset show?
- Selection effects: how was the evidence chosen?
- Survivorship bias: related — only seeing successes

When cherry picking IS present:
- Citing only studies that support a position while ignoring contradicting ones
- Selecting a favorable time period for a trend
- Quoting out of context to change meaning
- Presenting outliers as if they're typical
- Ignoring contradicting data without explanation
- "Look at these examples" when counterexamples are more numerous
- Selective reporting of outcomes (reporting only positive results)

When cherry picking is NOT present:
- The evidence is representative of the full dataset
- Contradicting evidence is acknowledged and addressed
- The selection criteria are stated and justified
- Case studies are presented as illustrative, not proof
- Limitations of the evidence are discussed
- The full picture is available and consistent with the claim
- Selection is based on quality, not on supporting the conclusion

Output JSON with: cherry_picking_present (bool), severity (none/mild/moderate/severe), claim (what is argued), evidence_presented (what data is shown), evidence_suppressed (what data is hidden), full_picture (what the complete data shows), selection_criteria (how evidence was chosen), recommendation (no_cherry_picking/mild_selectivity/significant_cherry_picking/major_data_suppression/present_full_picture)."""

CHERRY_PICKING_PROMPT = """Detect cherry picking:

Claim: {claim}
Evidence presented: {evidence_presented}
Evidence omitted: {evidence_omitted}
Full dataset: {full_dataset}
Domain: {domain}
Context: {context}

Has data been selectively presented to support a conclusion while hiding contradicting data? Return ONLY valid JSON."""


class CherryPickingService:
    """Detects cherry picking — selective presentation of favorable data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence_presented: str = "",
        evidence_omitted: str = "",
        full_dataset: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cherry picking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHERRY_PICKING_PROMPT.format(
                claim=claim,
                evidence_presented=evidence_presented or "Not specified",
                evidence_omitted=evidence_omitted or "Not specified",
                full_dataset=full_dataset or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHERRY_PICKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "cherry_picking_present": data.get("cherry_picking_present", False),
            "severity": data.get("severity", ""),
            "evidence_presented": data.get("evidence_presented", ""),
            "evidence_suppressed": data.get("evidence_suppressed", ""),
            "full_picture": data.get("full_picture", ""),
            "recommendation": data.get("recommendation", ""),
        }
