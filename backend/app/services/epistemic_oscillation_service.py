"""EpistemicOscillationService — Epistemic Oscillation Detection.

Detects epistemic oscillation — intellectual positions cycling between
states due to delayed feedback or overcorrection in reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OSCILLATION_SYSTEM = """You are an epistemic oscillation specialist. Given an intellectual position pattern, assess whether cycling between states occurs:

Key concepts:
- Epistemic oscillation: cycling between intellectual states
- Underdamping: oscillating around equilibrium
- Overdamping: slow return without oscillation
- Critical damping: fastest return without oscillation
- Natural frequency: inherent cycling rate
- Forced oscillation: external input driving cycles
- Limit cycle: self-sustaining oscillation

When epistemic oscillation IS present:
- Positions cycling between states
- Oscillating around an equilibrium position
- Overcorrection causing swing to opposite
- Inherent cycling rate in the system
- External inputs driving position changes
- Self-sustaining cycles without external input
- Delayed feedback causing instability

When stable equilibrium is present:
- Positions remaining at steady state
- No oscillation around equilibrium
- Corrections proportional and stable
- No inherent cycling tendency
- External inputs absorbed without cycling
- No self-sustaining patterns
- Immediate feedback maintaining stability

Output JSON with: oscillation_present (bool), severity (none/mild/moderate/severe), underdamping (what overcorrection), natural_frequency (what cycling rate), forced (what external driver), limit_cycle (what self-sustaining pattern), recommendation (stable_equilibrium/mild_oscillation/significant_oscillation/major_cycling/add_damping)."""

EPISTEMIC_OSCILLATION_PROMPT = """Detect epistemic oscillation:

Underdamping: {underdamping}
Natural frequency: {natural_frequency}
Forced: {forced}
Limit cycle: {limit_cycle}
Domain: {domain}
Context: {context}

Are intellectual positions cycling between states due to delayed feedback or overcorrection? Return ONLY valid JSON."""


class EpistemicOscillationService:
    """Detects epistemic oscillation — cycling between intellectual states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        underdamping: str,
        *,
        natural_frequency: str = "",
        forced: str = "",
        limit_cycle: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic oscillation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OSCILLATION_PROMPT.format(
                underdamping=underdamping,
                natural_frequency=natural_frequency or "Not specified",
                forced=forced or "Not specified",
                limit_cycle=limit_cycle or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OSCILLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "underdamping": underdamping[:200],
            "oscillation_present": data.get("oscillation_present", False),
            "severity": data.get("severity", ""),
            "natural_frequency": data.get("natural_frequency", ""),
            "forced": data.get("forced", ""),
            "limit_cycle": data.get("limit_cycle", ""),
            "recommendation": data.get("recommendation", ""),
        }
