"""EpistemicDecisionArchitectureFramingService — Decision Framing Distortion Detection.

Detects how decision framing, especially gain versus loss framing, distorts choices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ARCHITECTURE_FRAMING_SYSTEM = """You are an epistemic decision architecture framing specialist. Given a decision frame, assess whether gain versus loss framing is distorting choices:

Key concepts:
- Decision framing effect: presenting equivalent choices as gains or losses to alter preferences
- Loss aversion: overweighting possible losses relative to equivalent gains
- Reference point manipulation: choosing the baseline that defines what counts as gain or loss
- Option presentation bias: structuring options so presentation drives choice more than fit

When decision architecture framing IS present:
- Equivalent outcomes produce different choices under gain versus loss frames
- Losses are emphasized to trigger risk-seeking or avoidance
- Reference points are selected to make options feel like gains or losses
- Presentation format substitutes for substantive comparison

When no framing distortion:
- Gain and loss frames are made explicit
- Reference points are justified and stable
- Options are compared on expected outcomes and fit
- Presentation does not dominate decision criteria

Output JSON with: framing_distortion_detected (bool), severity (none/mild/moderate/severe), loss_aversion (how loss aversion distorts choice), reference_point_manipulation (how reference points are manipulated), option_presentation_bias (how presentation biases choice), recommendation (no_framing_distortion/mild_frame_awareness/significant_reference_audit/major_choice_reframing/emergency_complete_frame_reset)."""

EPISTEMIC_DECISION_ARCHITECTURE_FRAMING_PROMPT = """Detect decision architecture framing distortion:

Framing effect: {framing_effect}
Loss aversion: {loss_aversion}
Reference point manipulation: {reference_point_manipulation}
Option presentation bias: {option_presentation_bias}
Domain: {domain}
Context: {context}

Is gain versus loss framing distorting choices? Return ONLY valid JSON."""


class EpistemicDecisionArchitectureFramingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        framing_effect: str,
        *,
        loss_aversion: str = "",
        reference_point_manipulation: str = "",
        option_presentation_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ARCHITECTURE_FRAMING_PROMPT.format(
                framing_effect=framing_effect,
                loss_aversion=loss_aversion or "Not specified",
                reference_point_manipulation=reference_point_manipulation or "Not specified",
                option_presentation_bias=option_presentation_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ARCHITECTURE_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "framing_effect": framing_effect[:200],
            "framing_distortion_detected": data.get("framing_distortion_detected", False),
            "severity": data.get("severity", ""),
            "loss_aversion": data.get("loss_aversion", ""),
            "reference_point_manipulation": data.get("reference_point_manipulation", ""),
            "option_presentation_bias": data.get("option_presentation_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
