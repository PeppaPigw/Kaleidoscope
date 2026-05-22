"""EpistemicCircadianRhythmService — Epistemic Circadian Rhythm Detection.

Detects epistemic circadian rhythms — intellectual productivity following
cyclical patterns with peaks, troughs, and entrainment to external cues.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CIRCADIAN_RHYTHM_SYSTEM = """You are an epistemic circadian rhythm specialist. Given an intellectual productivity pattern, assess whether it follows cyclical rhythms:

Key concepts:
- Epistemic circadian rhythm: intellectual productivity following cyclical patterns
- Zeitgeber: external cue that entrains the rhythm
- Free-running period: natural cycle without external cues
- Phase shift: rhythm moving earlier or later
- Entrainment: synchronizing to external schedule
- Ultradian rhythm: shorter cycles within the main cycle
- Chronotype: individual's natural rhythm preference

When epistemic circadian rhythm IS present:
- Intellectual productivity following predictable cycles
- External cues entraining the intellectual rhythm
- Natural cycle evident without external scheduling
- Rhythm shifting earlier or later over time
- Synchronization to external intellectual schedules
- Shorter cycles within the main productivity cycle
- Individual natural rhythm preferences evident

When no rhythm is present:
- No cyclical productivity pattern
- No external entrainment
- No natural period
- No phase shifts
- No synchronization
- No ultradian cycles
- No chronotype preference

Output JSON with: circadian_rhythm_present (bool), severity (none/mild/moderate/severe), zeitgeber (what external cue), free_running_period (what natural cycle), phase_shift (what timing change), entrainment (what synchronization), recommendation (no_rhythm/mild_rhythm/significant_circadian_rhythm/major_cyclical_pattern/optimize_rhythm_alignment)."""

EPISTEMIC_CIRCADIAN_RHYTHM_PROMPT = """Detect epistemic circadian rhythm:

Zeitgeber: {zeitgeber}
Free-running period: {free_running_period}
Phase shift: {phase_shift}
Entrainment: {entrainment}
Domain: {domain}
Context: {context}

Is intellectual productivity following cyclical patterns with peaks, troughs, and entrainment? Return ONLY valid JSON."""


class EpistemicCircadianRhythmService:
    """Detects epistemic circadian rhythms — cyclical intellectual productivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        zeitgeber: str,
        *,
        free_running_period: str = "",
        phase_shift: str = "",
        entrainment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic circadian rhythm."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CIRCADIAN_RHYTHM_PROMPT.format(
                zeitgeber=zeitgeber,
                free_running_period=free_running_period or "Not specified",
                phase_shift=phase_shift or "Not specified",
                entrainment=entrainment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CIRCADIAN_RHYTHM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "zeitgeber": zeitgeber[:200],
            "circadian_rhythm_present": data.get("circadian_rhythm_present", False),
            "severity": data.get("severity", ""),
            "free_running_period": data.get("free_running_period", ""),
            "phase_shift": data.get("phase_shift", ""),
            "entrainment": data.get("entrainment", ""),
            "recommendation": data.get("recommendation", ""),
        }
