"""EvidenceWeightingService — Multi-Evidence Weighted Verdict.

Takes multiple pieces of evidence for/against a claim and weights them
by quality, relevance, and independence to produce a weighted verdict.
Handles the common problem of treating all evidence as equal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEIGHT_SYSTEM = """You are an evidence weighting specialist. Given a claim and multiple pieces of evidence, weight each piece by:
- Quality (methodology rigor, sample size, replication status)
- Relevance (how directly it bears on the claim)
- Independence (is it truly independent or derived from the same source/method?)
- Recency (is it still current?)
- Direction (supports, opposes, or neutral)

Then produce a weighted verdict that accounts for evidence quality, not just quantity.

Output JSON with: evidence_items (list of: description, direction (supports/opposes/neutral), quality_weight (0-1), relevance_weight (0-1), independence_score (0-1), recency_penalty (0-1, 1=current), effective_weight (combined weight), reasoning (why this weight)), weighted_verdict (what the evidence collectively says), verdict_confidence (0-1), strongest_for (best evidence supporting), strongest_against (best evidence opposing), evidence_gaps (what evidence is missing), naive_vs_weighted (how the conclusion changes when you weight properly vs count naively)."""

WEIGHT_PROMPT = """Weight this evidence for the claim:

Claim: {claim}
Evidence items:
{evidence_list}

Domain: {domain}

Weight each piece and produce a verdict. Return ONLY valid JSON."""


class EvidenceWeightingService:
    """Weights multiple evidence items to produce a weighted verdict."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def weight_evidence(
        self,
        claim: str,
        evidence: list[str],
        *,
        domain: str = "",
    ) -> dict:
        """Weight evidence items and produce a verdict."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        evidence_formatted = "\n".join(f"- {e}" for e in evidence[:10])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEIGHT_PROMPT.format(
                claim=claim,
                evidence_list=evidence_formatted,
                domain=domain or "general",
            ),
            system=WEIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        items = data.get("evidence_items", [])
        return {
            "claim": claim[:200],
            "evidence_count": len(items),
            "evidence_items": items,
            "weighted_verdict": data.get("weighted_verdict", ""),
            "verdict_confidence": data.get("verdict_confidence", 0),
            "strongest_for": data.get("strongest_for", ""),
            "strongest_against": data.get("strongest_against", ""),
            "evidence_gaps": data.get("evidence_gaps", []),
            "naive_vs_weighted": data.get("naive_vs_weighted", ""),
        }
