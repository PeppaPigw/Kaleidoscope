"""EpistemicEndocrineDisruptionService — Epistemic Endocrine Disruption Detection.

Detects epistemic endocrine disruption — external agents mimicking or blocking
intellectual regulatory signals, corrupting the signaling system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENDOCRINE_DISRUPTION_SYSTEM = """You are an epistemic endocrine disruption specialist. Given an intellectual signaling system, assess whether external agents corrupt regulatory signals:

Key concepts:
- Epistemic endocrine disruption: external agents corrupting intellectual signals
- Xenoestrogen: foreign substance mimicking natural signal
- Receptor blocking: external agent occupying receptor without activating
- Signal interference: disrupting normal signal transduction
- Bioaccumulation: disruptors accumulating over time
- Low-dose effect: disruption at surprisingly low concentrations
- Developmental window: critical periods of vulnerability

When epistemic endocrine disruption IS present:
- External agents mimicking natural intellectual signals
- Foreign substances occupying receptors without proper activation
- Normal signal transduction being disrupted
- Disruptors accumulating in the intellectual system over time
- Disruption occurring at surprisingly low exposure levels
- Critical developmental periods being exploited
- Regulatory system being corrupted from outside

When healthy signaling is present:
- No external signal mimicry
- Receptors occupied by legitimate signals only
- Normal signal transduction intact
- No accumulation of disruptors
- Appropriate dose-response relationships
- Developmental windows protected
- Regulatory system operating cleanly

Output JSON with: endocrine_disruption_present (bool), severity (none/mild/moderate/severe), xenoestrogen (what foreign mimicry), receptor_blocking (what occupancy without activation), signal_interference (what transduction disruption), bioaccumulation (what accumulation), recommendation (healthy_signaling/mild_disruption/significant_endocrine_disruption/major_signal_corruption/eliminate_disruptors)."""

EPISTEMIC_ENDOCRINE_DISRUPTION_PROMPT = """Detect epistemic endocrine disruption:

Xenoestrogen: {xenoestrogen}
Receptor blocking: {receptor_blocking}
Signal interference: {signal_interference}
Bioaccumulation: {bioaccumulation}
Domain: {domain}
Context: {context}

Are external agents mimicking or blocking intellectual regulatory signals, corrupting the system? Return ONLY valid JSON."""


class EpistemicEndocrineDisruptionService:
    """Detects epistemic endocrine disruption — external agents corrupting signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        xenoestrogen: str,
        *,
        receptor_blocking: str = "",
        signal_interference: str = "",
        bioaccumulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic endocrine disruption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENDOCRINE_DISRUPTION_PROMPT.format(
                xenoestrogen=xenoestrogen,
                receptor_blocking=receptor_blocking or "Not specified",
                signal_interference=signal_interference or "Not specified",
                bioaccumulation=bioaccumulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENDOCRINE_DISRUPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "xenoestrogen": xenoestrogen[:200],
            "endocrine_disruption_present": data.get("endocrine_disruption_present", False),
            "severity": data.get("severity", ""),
            "receptor_blocking": data.get("receptor_blocking", ""),
            "signal_interference": data.get("signal_interference", ""),
            "bioaccumulation": data.get("bioaccumulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
