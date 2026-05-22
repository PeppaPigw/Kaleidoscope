"""EpistemicVasopressorService — Epistemic Vasopressor Dependence Detection.

Detects epistemic vasopressor dependence — intellectual systems requiring
artificial pressure support to maintain circulation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VASOPRESSOR_SYSTEM = """You are an epistemic vasopressor specialist. Given intellectual pressure failure, assess vasopressor dependence:

Key concepts:
- Epistemic vasopressor: artificial agent maintaining intellectual pressure
- Dose escalation: needing increasing support over time
- Refractory shock: not responding to pressure support
- Tachyphylaxis: diminishing response to same dose
- Multi-agent support: needing multiple pressors simultaneously
- Weaning protocol: gradual reduction of support
- End-organ damage: organs failing from low pressure

When epistemic vasopressor dependence IS present:
- Cannot maintain intellectual pressure without support
- Escalating doses needed
- Not responding to current support
- Diminishing response over time
- Multiple support agents needed
- Cannot reduce support without collapse
- Organs failing from inadequate pressure

When no vasopressor dependence:
- Self-maintaining intellectual pressure
- No external support needed
- Responsive to normal stimuli
- Stable response patterns
- Single system adequate
- Independent function maintained
- All organs well-perfused

Output JSON with: vasopressor_dependence (bool), severity (none/mild/moderate/severe), dose_trajectory (what escalation pattern), refractory_signs (what non-response), tachyphylaxis (what diminishing response), organ_damage (what end-organ effects), recommendation (no_vasopressor_needed/mild_support/significant_pressor/major_multi_agent/emergency_refractory_shock)."""

EPISTEMIC_VASOPRESSOR_PROMPT = """Detect epistemic vasopressor dependence:

Dose trajectory: {dose_trajectory}
Refractory signs: {refractory_signs}
Tachyphylaxis: {tachyphylaxis}
Organ damage: {organ_damage}
Domain: {domain}
Context: {context}

Does the intellectual system require artificial pressure support? Return ONLY valid JSON."""


class EpistemicVasopressorService:
    """Detects epistemic vasopressor dependence — needing artificial pressure support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dose_trajectory: str,
        *,
        refractory_signs: str = "",
        tachyphylaxis: str = "",
        organ_damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vasopressor dependence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VASOPRESSOR_PROMPT.format(
                dose_trajectory=dose_trajectory,
                refractory_signs=refractory_signs or "Not specified",
                tachyphylaxis=tachyphylaxis or "Not specified",
                organ_damage=organ_damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VASOPRESSOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dose_trajectory": dose_trajectory[:200],
            "vasopressor_dependence": data.get("vasopressor_dependence", False),
            "severity": data.get("severity", ""),
            "refractory_signs": data.get("refractory_signs", ""),
            "tachyphylaxis": data.get("tachyphylaxis", ""),
            "organ_damage": data.get("organ_damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
