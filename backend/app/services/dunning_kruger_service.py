"""DunningKrugerService — Competence-Confidence Calibration.

Detects Dunning-Kruger patterns — where low competence correlates
with high confidence (and vice versa). The unskilled overestimate
their ability because they lack the metacognitive skill to recognize
their incompetence. Experts underestimate because they assume others
find it equally easy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DUNNING_KRUGER_SYSTEM = """You are a competence-confidence calibration specialist. Given a claim or assessment, detect whether Dunning-Kruger effects are present:

Key patterns:
- Mount Stupid: high confidence with low competence (most dangerous)
- Valley of Despair: low confidence despite growing competence
- Slope of Enlightenment: calibrating confidence to actual ability
- Plateau of Sustainability: expert-level confidence, slightly below actual ability

Assess:
- Is the confidence level appropriate for the demonstrated competence?
- Are there signs of metacognitive failure (not knowing what you don't know)?
- Is there false consensus (assuming everyone knows/doesn't know what you do)?
- Are credentials being confused with competence?
- Is domain-specific expertise being overgeneralized?

Output JSON with: dunning_kruger_present (bool), pattern (mount_stupid/valley_of_despair/slope_of_enlightenment/well_calibrated), confidence_level (0-1 — expressed confidence), estimated_competence (0-1 — likely actual competence), calibration_gap (confidence minus competence, positive = overconfident), metacognitive_failure (bool — unable to recognize own incompetence?), false_consensus (bool — assuming others share their level?), domain_overgeneralization (bool — applying expertise from one domain to another?), credential_competence_confusion (bool — using credentials as proxy for ability?), unknown_unknowns (what they likely don't know they don't know), evidence_of_competence (what actually demonstrates their ability level), evidence_of_overconfidence (what suggests inflated self-assessment), evidence_of_underconfidence (what suggests deflated self-assessment), who_is_affected (who suffers from the miscalibration), correction_difficulty (how hard it is to recalibrate — easy/moderate/hard/very_hard), recommendation (well_calibrated/mild_overconfidence/significant_overconfidence/dangerous_incompetence/undervaluing_expertise)."""

DUNNING_KRUGER_PROMPT = """Detect Dunning-Kruger effect:

Claim/Assessment: {claim}
Source confidence: {confidence}
Evidence of competence: {evidence}
Domain: {domain}
Track record: {track_record}
Context: {context}

Is there a competence-confidence miscalibration? Return ONLY valid JSON."""


class DunningKrugerService:
    """Detects Dunning-Kruger competence-confidence miscalibration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        confidence: str = "",
        evidence: str = "",
        domain: str = "",
        track_record: str = "",
        context: str = "",
    ) -> dict:
        """Detect Dunning-Kruger effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DUNNING_KRUGER_PROMPT.format(
                claim=claim,
                confidence=confidence or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                track_record=track_record or "Not specified",
                context=context or "No additional context",
            ),
            system=DUNNING_KRUGER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "dunning_kruger_present": data.get("dunning_kruger_present", False),
            "pattern": data.get("pattern", ""),
            "confidence_level": data.get("confidence_level", 0),
            "estimated_competence": data.get("estimated_competence", 0),
            "calibration_gap": data.get("calibration_gap", 0),
            "metacognitive_failure": data.get("metacognitive_failure", False),
            "false_consensus": data.get("false_consensus", False),
            "domain_overgeneralization": data.get("domain_overgeneralization", False),
            "credential_competence_confusion": data.get("credential_competence_confusion", False),
            "unknown_unknowns": data.get("unknown_unknowns", ""),
            "evidence_of_competence": data.get("evidence_of_competence", ""),
            "evidence_of_overconfidence": data.get("evidence_of_overconfidence", ""),
            "evidence_of_underconfidence": data.get("evidence_of_underconfidence", ""),
            "who_is_affected": data.get("who_is_affected", ""),
            "correction_difficulty": data.get("correction_difficulty", ""),
            "recommendation": data.get("recommendation", ""),
        }
