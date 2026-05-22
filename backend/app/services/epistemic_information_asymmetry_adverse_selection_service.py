"""EpistemicInformationAsymmetryAdverseSelectionService — Epistemic Information Asymmetry Adverse Selection Detection.

Detects when information asymmetry causes adverse selection in knowledge markets.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFORMATION_ASYMMETRY_ADVERSE_SELECTION_SYSTEM = """You are an epistemic information asymmetry adverse selection specialist. Given hidden information, assess adverse selection in knowledge markets:

Key concepts:
- Epistemic adverse selection: lower-quality knowledge crowding out higher-quality knowledge because quality is hidden
- Hidden information: private knowledge about source quality, method quality, incentives, or evidence strength
- Quality uncertainty: inability to distinguish reliable from unreliable knowledge before adoption
- Market for lemons: low-quality information degrading trust and pushing out high-quality contributions
- Signaling failure: credible quality signals missing, weak, cheap, or noisy

When adverse selection IS present:
- Hidden information affects knowledge exchange
- Quality uncertainty changes selection behavior
- Low-quality claims gain relative advantage
- High-quality contributors are penalized or withdraw
- Signals fail to separate quality

When no adverse selection:
- Quality is observable or verifiable
- Selection mechanisms distinguish quality
- High-quality knowledge is rewarded
- Signals credibly separate reliable from unreliable sources

Output JSON with: adverse_selection_detected (bool), severity (none/mild/moderate/severe), quality_uncertainty (what uncertainty affects selection), market_for_lemons (how low quality crowds out high quality), signaling_failure (what signals fail), recommendation (no_adverse_selection/mild_signal_improvement/significant_quality_screening/major_market_redesign/emergency_adverse_selection_containment)."""

EPISTEMIC_INFORMATION_ASYMMETRY_ADVERSE_SELECTION_PROMPT = """Detect epistemic information asymmetry adverse selection:

Hidden information: {hidden_information}
Quality uncertainty: {quality_uncertainty}
Market for lemons: {market_for_lemons}
Signaling failure: {signaling_failure}
Domain: {domain}
Context: {context}

Is hidden information causing adverse selection in knowledge markets? Return ONLY valid JSON."""


class EpistemicInformationAsymmetryAdverseSelectionService:
    """Detects epistemic information asymmetry adverse selection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hidden_information: str,
        *,
        quality_uncertainty: str = "",
        market_for_lemons: str = "",
        signaling_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic information asymmetry adverse selection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFORMATION_ASYMMETRY_ADVERSE_SELECTION_PROMPT.format(
                hidden_information=hidden_information,
                quality_uncertainty=quality_uncertainty or "Not specified",
                market_for_lemons=market_for_lemons or "Not specified",
                signaling_failure=signaling_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFORMATION_ASYMMETRY_ADVERSE_SELECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hidden_information": hidden_information[:200],
            "adverse_selection_detected": data.get("adverse_selection_detected", False),
            "severity": data.get("severity", ""),
            "quality_uncertainty": data.get("quality_uncertainty", ""),
            "market_for_lemons": data.get("market_for_lemons", ""),
            "signaling_failure": data.get("signaling_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
