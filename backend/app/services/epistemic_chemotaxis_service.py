"""EpistemicChemotaxisService — Epistemic Chemotaxis Detection.

Detects epistemic chemotaxis — ideas moving toward or away from
intellectual chemical signals in their environment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CHEMOTAXIS_SYSTEM = """You are an epistemic chemotaxis specialist. Given an idea movement pattern, assess whether ideas move toward or away from intellectual signals:

Key concepts:
- Epistemic chemotaxis: ideas moving toward/away from signals
- Attractant: intellectual signal drawing ideas toward it
- Repellent: intellectual signal pushing ideas away
- Gradient: concentration of signal varying across space
- Sensitivity: how responsive ideas are to signals
- Adaptation: ideas becoming less responsive over time
- Tumble: random direction changes when signal is lost

When epistemic chemotaxis IS present:
- Ideas moving toward or away from intellectual signals
- Intellectual signals drawing ideas in specific directions
- Intellectual signals pushing ideas away from areas
- Signal concentration varying across intellectual space
- Ideas highly responsive to environmental signals
- Ideas becoming less responsive to constant signals
- Random direction changes when signal is lost

When autonomous movement is present:
- Ideas moving independently of environmental signals
- No signals drawing ideas in directions
- No signals pushing ideas away
- Uniform intellectual environment
- Ideas not responsive to environmental signals
- Consistent responsiveness over time
- Directed movement regardless of signals

Output JSON with: chemotaxis_present (bool), severity (none/mild/moderate/severe), signal (what intellectual signal), direction (toward or away), gradient (what concentration varies), adaptation (what desensitization occurs), recommendation (autonomous_movement/mild_signal_response/significant_chemotaxis/major_signal_driven/assess_signal_validity)."""

EPISTEMIC_CHEMOTAXIS_PROMPT = """Detect epistemic chemotaxis:

Signal: {signal}
Direction: {direction}
Gradient: {gradient}
Adaptation: {adaptation}
Domain: {domain}
Context: {context}

Are ideas moving toward or away from intellectual chemical signals in their environment? Return ONLY valid JSON."""


class EpistemicChemotaxisService:
    """Detects epistemic chemotaxis — signal-driven idea movement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        signal: str,
        *,
        direction: str = "",
        gradient: str = "",
        adaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic chemotaxis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CHEMOTAXIS_PROMPT.format(
                signal=signal,
                direction=direction or "Not specified",
                gradient=gradient or "Not specified",
                adaptation=adaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CHEMOTAXIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "signal": signal[:200],
            "chemotaxis_present": data.get("chemotaxis_present", False),
            "severity": data.get("severity", ""),
            "direction": data.get("direction", ""),
            "gradient": data.get("gradient", ""),
            "adaptation": data.get("adaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }
