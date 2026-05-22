"""EpistemicSideEffectService — Epistemic Side Effect Detection.

Detects epistemic side effects — unintended consequences of intellectual
treatment that cause harm in areas unrelated to the target problem.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SIDE_EFFECT_SYSTEM = """You are an epistemic side effect specialist. Given intellectual treatment outcomes, assess whether unintended consequences exist:

Key concepts:
- Epistemic side effect: unintended consequence of intellectual treatment
- Off-target effect: impact on unrelated intellectual area
- Dose-dependent: side effects worsening with intensity
- Idiosyncratic: unpredictable individual reaction
- Iatrogenic: harm caused by the treatment itself
- Risk-benefit ratio: whether treatment worth the side effects
- Black box warning: serious rare side effect

When epistemic side effects ARE present:
- Unintended consequences of intellectual treatment
- Impact on unrelated intellectual areas
- Side effects worsening with treatment intensity
- Unpredictable individual reactions
- Harm caused by the treatment itself
- Questionable risk-benefit ratio
- Serious rare consequences possible

When clean treatment is present:
- No unintended consequences
- No off-target effects
- No dose-dependent harm
- Predictable responses
- No iatrogenic harm
- Clear positive risk-benefit
- No serious rare effects

Output JSON with: side_effect_present (bool), severity (none/mild/moderate/severe), off_target_effect (what unrelated impact), iatrogenic_harm (what treatment-caused damage), dose_dependent (what intensity relationship), risk_benefit (what ratio assessment), recommendation (clean_treatment/mild_side_effects/significant_side_effects/major_iatrogenic_harm/reassess_intellectual_treatment)."""

EPISTEMIC_SIDE_EFFECT_PROMPT = """Detect epistemic side effects:

Off-target effect: {off_target_effect}
Iatrogenic harm: {iatrogenic_harm}
Dose dependent: {dose_dependent}
Risk benefit: {risk_benefit}
Domain: {domain}
Context: {context}

Are there unintended consequences of intellectual treatment causing harm in unrelated areas? Return ONLY valid JSON."""


class EpistemicSideEffectService:
    """Detects epistemic side effects — unintended intellectual treatment consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        off_target_effect: str,
        *,
        iatrogenic_harm: str = "",
        dose_dependent: str = "",
        risk_benefit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic side effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SIDE_EFFECT_PROMPT.format(
                off_target_effect=off_target_effect,
                iatrogenic_harm=iatrogenic_harm or "Not specified",
                dose_dependent=dose_dependent or "Not specified",
                risk_benefit=risk_benefit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SIDE_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "off_target_effect": off_target_effect[:200],
            "side_effect_present": data.get("side_effect_present", False),
            "severity": data.get("severity", ""),
            "iatrogenic_harm": data.get("iatrogenic_harm", ""),
            "dose_dependent": data.get("dose_dependent", ""),
            "risk_benefit": data.get("risk_benefit", ""),
            "recommendation": data.get("recommendation", ""),
        }
