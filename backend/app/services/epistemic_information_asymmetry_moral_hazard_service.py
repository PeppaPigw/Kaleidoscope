"""EpistemicInformationAsymmetryMoralHazardService — Epistemic Information Asymmetry Moral Hazard Detection.

Detects when unobservable actions create moral hazard in epistemic processes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFORMATION_ASYMMETRY_MORAL_HAZARD_SYSTEM = """You are an epistemic information asymmetry moral hazard specialist. Given unobservable effort, assess moral hazard in epistemic processes:

Key concepts:
- Epistemic moral hazard: reduced care, rigor, or honesty when actions are hidden from evaluators
- Unobservable effort: hidden research, verification, reasoning, or review effort
- Monitoring gap: inability to observe whether epistemic work was actually performed
- Incentive misalignment: rewards favor outputs, speed, status, or persuasion over truth-seeking effort
- Accountability void: weak consequences for low effort, negligent reasoning, or selective verification

When moral hazard IS present:
- Effort or care is hidden
- Monitoring cannot distinguish diligent from negligent work
- Incentives reward low-rigor behavior
- Accountability is absent or symbolic
- Epistemic quality is degraded by hidden actions

When no moral hazard:
- Effort is observable or auditable
- Monitoring detects low-rigor behavior
- Incentives reward quality and verification
- Accountability follows epistemic responsibility

Output JSON with: moral_hazard_detected (bool), severity (none/mild/moderate/severe), monitoring_gap (what cannot be observed), incentive_misalignment (what incentives distort effort), accountability_void (what accountability is missing), recommendation (no_moral_hazard/mild_monitoring_improvement/significant_incentive_alignment/major_accountability_redesign/emergency_moral_hazard_containment)."""

EPISTEMIC_INFORMATION_ASYMMETRY_MORAL_HAZARD_PROMPT = """Detect epistemic information asymmetry moral hazard:

Unobservable effort: {unobservable_effort}
Monitoring gap: {monitoring_gap}
Incentive misalignment: {incentive_misalignment}
Accountability void: {accountability_void}
Domain: {domain}
Context: {context}

Are unobservable actions creating moral hazard in epistemic processes? Return ONLY valid JSON."""


class EpistemicInformationAsymmetryMoralHazardService:
    """Detects epistemic information asymmetry moral hazard."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unobservable_effort: str,
        *,
        monitoring_gap: str = "",
        incentive_misalignment: str = "",
        accountability_void: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic information asymmetry moral hazard."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFORMATION_ASYMMETRY_MORAL_HAZARD_PROMPT.format(
                unobservable_effort=unobservable_effort,
                monitoring_gap=monitoring_gap or "Not specified",
                incentive_misalignment=incentive_misalignment or "Not specified",
                accountability_void=accountability_void or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFORMATION_ASYMMETRY_MORAL_HAZARD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unobservable_effort": unobservable_effort[:200],
            "moral_hazard_detected": data.get("moral_hazard_detected", False),
            "severity": data.get("severity", ""),
            "monitoring_gap": data.get("monitoring_gap", ""),
            "incentive_misalignment": data.get("incentive_misalignment", ""),
            "accountability_void": data.get("accountability_void", ""),
            "recommendation": data.get("recommendation", ""),
        }
