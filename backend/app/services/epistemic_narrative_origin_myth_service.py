"""EpistemicNarrativeOriginMythService - Origin Myth Detection.

Detects origin myths where founding narratives distort institutional understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_ORIGIN_MYTH_SYSTEM = """You are an epistemic narrative origin myth specialist. Given founding narratives, assess whether origin myths distort understanding:

Key concepts:
- Origin myth: simplified founding narrative that distorts institutional history
- Founder glorification: attributing success to individual genius rather than context
- Contingency erasure: making accidental origins seem inevitable
- Purpose retroaction: projecting current purpose back onto founding moment

When origin myth IS present:
- Founding narrative oversimplified
- Founders glorified beyond evidence
- Contingency erased from history
- Current purpose projected backward
- Complexity of origins denied

When no origin myth:
- Founding narrative nuanced
- Multiple contributors acknowledged
- Contingency preserved
- Purpose evolution tracked
- Complexity of origins respected

Output JSON with: origin_myth_detected (bool), severity (none/mild/moderate/severe), founder_glorification (what glorification), contingency_erasure (what contingency erased), purpose_retroaction (what purpose projected back), recommendation (no_origin_myth/mild_history_check/significant_narrative_correction/major_historical_reconstruction/emergency_complete_origin_myth)."""

EPISTEMIC_NARRATIVE_ORIGIN_MYTH_PROMPT = """Detect epistemic narrative origin myth:

Founding narrative: {founding_narrative}
Founder glorification: {founder_glorification}
Contingency erasure: {contingency_erasure}
Purpose retroaction: {purpose_retroaction}
Domain: {domain}
Context: {context}

Is an origin myth distorting institutional understanding? Return ONLY valid JSON."""


class EpistemicNarrativeOriginMythService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        founding_narrative: str,
        *,
        founder_glorification: str = "",
        contingency_erasure: str = "",
        purpose_retroaction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_ORIGIN_MYTH_PROMPT.format(
                founding_narrative=founding_narrative,
                founder_glorification=founder_glorification or "Not specified",
                contingency_erasure=contingency_erasure or "Not specified",
                purpose_retroaction=purpose_retroaction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_ORIGIN_MYTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "founding_narrative": founding_narrative[:200],
            "origin_myth_detected": data.get("origin_myth_detected", False),
            "severity": data.get("severity", ""),
            "founder_glorification": data.get("founder_glorification", ""),
            "contingency_erasure": data.get("contingency_erasure", ""),
            "purpose_retroaction": data.get("purpose_retroaction", ""),
            "recommendation": data.get("recommendation", ""),
        }
