"""EpistemicNystagmusService — Epistemic Nystagmus Detection.

Detects epistemic nystagmus — involuntary rapid oscillation between
intellectual viewpoints preventing stable focus on any single perspective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NYSTAGMUS_SYSTEM = """You are an epistemic nystagmus specialist. Given involuntary intellectual oscillation, assess nystagmus:

Key concepts:
- Epistemic nystagmus: involuntary rapid oscillation between viewpoints
- Jerk nystagmus: fast phase in one direction, slow drift back
- Pendular nystagmus: equal speed oscillation both directions
- Null point: position where oscillation minimizes
- Vestibular origin: balance system causing oscillation
- Congenital: present from intellectual formation
- Acquired: developed after intellectual maturity

When epistemic nystagmus IS present:
- Involuntary rapid oscillation between viewpoints
- Unable to maintain stable focus
- Fast phase jerking in one direction
- Equal speed pendular movement
- No null point of stability found
- Balance system disrupted
- Oscillation preventing clear vision

When no nystagmus:
- Stable intellectual focus maintained
- No involuntary oscillation
- Smooth tracking of ideas
- Steady fixation possible
- Balance system intact
- Clear stable vision
- Voluntary perspective shifts only

Output JSON with: nystagmus_detected (bool), severity (none/mild/moderate/severe), oscillation_type (what movement pattern), frequency (what speed), null_point (what stability position), origin (what cause), recommendation (no_nystagmus/mild_monitoring/significant_null_point_therapy/major_medication/emergency_acute_onset)."""

EPISTEMIC_NYSTAGMUS_PROMPT = """Detect epistemic nystagmus:

Oscillation type: {oscillation_type}
Frequency: {frequency}
Null point: {null_point}
Origin: {origin}
Domain: {domain}
Context: {context}

Is there involuntary rapid oscillation between intellectual viewpoints preventing stable focus? Return ONLY valid JSON."""


class EpistemicNystagmusService:
    """Detects epistemic nystagmus — involuntary oscillation between viewpoints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        oscillation_type: str,
        *,
        frequency: str = "",
        null_point: str = "",
        origin: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nystagmus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NYSTAGMUS_PROMPT.format(
                oscillation_type=oscillation_type,
                frequency=frequency or "Not specified",
                null_point=null_point or "Not specified",
                origin=origin or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NYSTAGMUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "oscillation_type": oscillation_type[:200],
            "nystagmus_detected": data.get("nystagmus_detected", False),
            "severity": data.get("severity", ""),
            "frequency": data.get("frequency", ""),
            "null_point": data.get("null_point", ""),
            "origin": data.get("origin", ""),
            "recommendation": data.get("recommendation", ""),
        }
