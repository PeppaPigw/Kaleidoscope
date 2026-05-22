"""EpistemicToleranceBuildup — Epistemic Tolerance Buildup Detection.

Detects epistemic tolerance buildup — decreasing effectiveness of repeated
intellectual interventions requiring ever-larger doses for same effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TOLERANCE_BUILDUP_SYSTEM = """You are an epistemic tolerance buildup specialist. Given intellectual intervention history, assess whether effectiveness is decreasing:

Key concepts:
- Epistemic tolerance buildup: decreasing effectiveness of repeated interventions
- Tachyphylaxis: rapid tolerance development
- Dose escalation: needing more for same effect
- Cross-tolerance: tolerance to one extending to similar interventions
- Receptor downregulation: reduced sensitivity to intervention
- Drug holiday: break to restore sensitivity
- Ceiling effect: maximum response regardless of dose

When epistemic tolerance buildup IS present:
- Decreasing effectiveness of repeated interventions
- Rapid tolerance development
- Needing more intellectual input for same effect
- Tolerance extending to similar approaches
- Reduced sensitivity to intervention
- Need for breaks to restore sensitivity
- Maximum response reached regardless of effort

When normal sensitivity is present:
- Consistent effectiveness
- No tolerance development
- Same dose produces same effect
- No cross-tolerance
- Full receptor sensitivity
- No drug holiday needed
- Linear dose-response

Output JSON with: tolerance_buildup_present (bool), severity (none/mild/moderate/severe), tachyphylaxis (what rapid tolerance), dose_escalation (what increasing need), cross_tolerance (what extended tolerance), receptor_downregulation (what reduced sensitivity), recommendation (normal_sensitivity/mild_tolerance/significant_tolerance_buildup/major_effectiveness_loss/intellectual_drug_holiday)."""

EPISTEMIC_TOLERANCE_BUILDUP_PROMPT = """Detect epistemic tolerance buildup:

Tachyphylaxis: {tachyphylaxis}
Dose escalation: {dose_escalation}
Cross tolerance: {cross_tolerance}
Receptor downregulation: {receptor_downregulation}
Domain: {domain}
Context: {context}

Is there decreasing effectiveness of repeated intellectual interventions? Return ONLY valid JSON."""


class EpistemicToleranceBuildupService:
    """Detects epistemic tolerance buildup — decreasing intervention effectiveness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tachyphylaxis: str,
        *,
        dose_escalation: str = "",
        cross_tolerance: str = "",
        receptor_downregulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tolerance buildup."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TOLERANCE_BUILDUP_PROMPT.format(
                tachyphylaxis=tachyphylaxis,
                dose_escalation=dose_escalation or "Not specified",
                cross_tolerance=cross_tolerance or "Not specified",
                receptor_downregulation=receptor_downregulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TOLERANCE_BUILDUP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tachyphylaxis": tachyphylaxis[:200],
            "tolerance_buildup_present": data.get("tolerance_buildup_present", False),
            "severity": data.get("severity", ""),
            "dose_escalation": data.get("dose_escalation", ""),
            "cross_tolerance": data.get("cross_tolerance", ""),
            "receptor_downregulation": data.get("receptor_downregulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
