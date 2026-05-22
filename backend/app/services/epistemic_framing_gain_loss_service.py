"""EpistemicFramingGainLossService — Epistemic Gain/Loss Framing Detection.

Detects epistemic framing gain/loss manipulation — framing identical
information as gain vs loss to manipulate perception and decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAMING_GAIN_LOSS_SYSTEM = """You are an epistemic framing gain/loss specialist. Given gain/loss framing, assess manipulation:

Key concepts:
- Epistemic gain/loss framing: identical info framed as gain vs loss
- Loss aversion exploitation: framing as loss to trigger stronger response
- Gain minimization: framing gains to seem smaller than they are
- Risk framing asymmetry: framing risk differently for gain vs loss scenarios
- Survival vs mortality framing: same data framed as survival rate vs death rate
- Savings vs cost framing: same amount framed as savings vs cost
- Progress vs remaining framing: same status framed as progress vs remaining

When epistemic gain/loss framing IS present:
- Identical info framed as gain vs loss
- Loss aversion exploited
- Gains minimized
- Risk framing asymmetric
- Survival/mortality switched
- Savings/cost switched
- Progress/remaining switched

When no gain/loss framing manipulation:
- Framing neutral or both perspectives given
- Loss aversion not exploited
- Gains and losses proportional
- Risk framing consistent
- Both framings presented
- Context determines appropriate frame
- Manipulation absent

Output JSON with: gain_loss_framing_detected (bool), severity (none/mild/moderate/severe), loss_aversion_exploitation (what loss aversion exploited), gain_minimization (what gains minimized), risk_framing_asymmetry (what risk framing asymmetric), frame_switching (what frames switched), recommendation (no_gain_loss_framing/mild_dual_framing/significant_frame_neutralization/major_intensive_framing_audit/emergency_complete_gain_loss_manipulation)."""

EPISTEMIC_FRAMING_GAIN_LOSS_PROMPT = """Detect epistemic gain/loss framing manipulation:

Loss aversion exploitation: {loss_aversion_exploitation}
Gain minimization: {gain_minimization}
Risk framing asymmetry: {risk_framing_asymmetry}
Frame switching: {frame_switching}
Domain: {domain}
Context: {context}

Is identical information being framed as gain vs loss to manipulate perception? Return ONLY valid JSON."""


class EpistemicFramingGainLossService:
    """Detects epistemic gain/loss framing — manipulative frame choice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        loss_aversion_exploitation: str,
        *,
        gain_minimization: str = "",
        risk_framing_asymmetry: str = "",
        frame_switching: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gain/loss framing manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAMING_GAIN_LOSS_PROMPT.format(
                loss_aversion_exploitation=loss_aversion_exploitation,
                gain_minimization=gain_minimization or "Not specified",
                risk_framing_asymmetry=risk_framing_asymmetry or "Not specified",
                frame_switching=frame_switching or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAMING_GAIN_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "loss_aversion_exploitation": loss_aversion_exploitation[:200],
            "gain_loss_framing_detected": data.get("gain_loss_framing_detected", False),
            "severity": data.get("severity", ""),
            "gain_minimization": data.get("gain_minimization", ""),
            "risk_framing_asymmetry": data.get("risk_framing_asymmetry", ""),
            "frame_switching": data.get("frame_switching", ""),
            "recommendation": data.get("recommendation", ""),
        }
