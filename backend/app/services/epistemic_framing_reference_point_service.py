"""EpistemicFramingReferencePointService — Epistemic Reference Point Framing Detection.

Detects epistemic framing reference point manipulation — choosing reference
points that distort comparison and evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAMING_REFERENCE_POINT_SYSTEM = """You are an epistemic framing reference point specialist. Given reference point manipulation, assess comparison distortion:

Key concepts:
- Epistemic reference point framing: choosing reference points to distort comparison
- Anchor manipulation: setting anchors that bias subsequent judgment
- Baseline cherry-picking: choosing baselines that make changes look better/worse
- Comparison target selection: choosing comparison targets strategically
- Status quo framing: framing current state as natural reference point
- Aspiration framing: framing against aspirational targets to create dissatisfaction
- Historical reference manipulation: choosing historical reference points strategically

When epistemic reference point framing IS present:
- Reference points strategically chosen
- Anchors manipulated
- Baselines cherry-picked
- Comparison targets biased
- Status quo framed as natural
- Aspirational targets creating dissatisfaction
- Historical references manipulated

When no reference point manipulation:
- Reference points appropriate
- Anchors natural
- Baselines justified
- Comparisons fair
- Status quo questioned
- Targets realistic
- Historical references representative

Output JSON with: reference_point_framing_detected (bool), severity (none/mild/moderate/severe), anchor_manipulation (what anchors manipulated), baseline_cherry_picking (what baselines cherry-picked), comparison_target_bias (what targets biased), historical_reference_manipulation (what historical references manipulated), recommendation (no_reference_point_framing/mild_reference_justification/significant_multiple_references/major_intensive_reference_audit/emergency_complete_reference_manipulation)."""

EPISTEMIC_FRAMING_REFERENCE_POINT_PROMPT = """Detect epistemic reference point framing manipulation:

Anchor manipulation: {anchor_manipulation}
Baseline cherry picking: {baseline_cherry_picking}
Comparison target bias: {comparison_target_bias}
Historical reference manipulation: {historical_reference_manipulation}
Domain: {domain}
Context: {context}

Are reference points being chosen to distort comparison and evaluation? Return ONLY valid JSON."""


class EpistemicFramingReferencePointService:
    """Detects epistemic reference point framing — comparison distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        anchor_manipulation: str,
        *,
        baseline_cherry_picking: str = "",
        comparison_target_bias: str = "",
        historical_reference_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reference point framing manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAMING_REFERENCE_POINT_PROMPT.format(
                anchor_manipulation=anchor_manipulation,
                baseline_cherry_picking=baseline_cherry_picking or "Not specified",
                comparison_target_bias=comparison_target_bias or "Not specified",
                historical_reference_manipulation=historical_reference_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAMING_REFERENCE_POINT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "anchor_manipulation": anchor_manipulation[:200],
            "reference_point_framing_detected": data.get("reference_point_framing_detected", False),
            "severity": data.get("severity", ""),
            "baseline_cherry_picking": data.get("baseline_cherry_picking", ""),
            "comparison_target_bias": data.get("comparison_target_bias", ""),
            "historical_reference_manipulation": data.get("historical_reference_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
