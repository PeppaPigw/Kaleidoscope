"""EpistemicHyperthyroidismService — Epistemic Hyperthyroidism Detection.

Detects epistemic hyperthyroidism — overactive intellectual metabolism
where everything races from excessive signaling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYPERTHYROIDISM_SYSTEM = """You are an epistemic hyperthyroidism specialist. Given overactive intellectual metabolism, assess hyperthyroidism:

Key concepts:
- Epistemic hyperthyroidism: overactive intellectual metabolism
- Metabolic acceleration: all processes racing unsustainably
- Thyroid storm: dangerous metabolic crisis
- Tremor: inability to hold intellectual position steady
- Heat intolerance: overheating from excess energy
- Weight loss: burning through intellectual reserves
- Antithyroid therapy: suppressing excessive signaling

When epistemic hyperthyroidism IS present:
- Intellectual metabolism overactive
- All processes racing unsustainably
- Risk of metabolic crisis
- Unable to hold steady position
- Overheating from excess energy
- Burning through reserves
- Signal suppression needed

When no hyperthyroidism:
- Normal intellectual metabolism
- Processes at sustainable speed
- No crisis risk
- Steady intellectual position
- Normal energy levels
- Reserves maintained
- No suppression needed

Output JSON with: hyperthyroidism_detected (bool), severity (none/mild/moderate/severe), metabolic_rate (what speed), signal_excess (what over-signaling), stability (what tremor), reserve_status (what depletion), recommendation (no_hyperthyroidism/mild_monitoring/significant_antithyroid/major_ablation/emergency_thyroid_storm)."""

EPISTEMIC_HYPERTHYROIDISM_PROMPT = """Detect epistemic hyperthyroidism:

Metabolic rate: {metabolic_rate}
Signal excess: {signal_excess}
Stability: {stability}
Reserve status: {reserve_status}
Domain: {domain}
Context: {context}

Is there overactive intellectual metabolism from excessive signaling? Return ONLY valid JSON."""


class EpistemicHyperthyroidismService:
    """Detects epistemic hyperthyroidism — overactive intellectual metabolism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metabolic_rate: str,
        *,
        signal_excess: str = "",
        stability: str = "",
        reserve_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hyperthyroidism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYPERTHYROIDISM_PROMPT.format(
                metabolic_rate=metabolic_rate,
                signal_excess=signal_excess or "Not specified",
                stability=stability or "Not specified",
                reserve_status=reserve_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYPERTHYROIDISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metabolic_rate": metabolic_rate[:200],
            "hyperthyroidism_detected": data.get("hyperthyroidism_detected", False),
            "severity": data.get("severity", ""),
            "signal_excess": data.get("signal_excess", ""),
            "stability": data.get("stability", ""),
            "reserve_status": data.get("reserve_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
