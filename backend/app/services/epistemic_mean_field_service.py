"""EpistemicMeanFieldService — Epistemic Mean Field Detection.

Detects epistemic mean field — replacing complex many-body intellectual
interactions with an effective average field that each idea experiences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEAN_FIELD_SYSTEM = """You are an epistemic mean field specialist. Given intellectual interactions, assess whether complex interactions are replaced by an average field:

Key concepts:
- Epistemic mean field: replacing complex interactions with average field
- Self-consistency: field determined by the state it creates
- Order parameter: quantity measuring degree of order
- Critical temperature: point where mean field breaks down
- Fluctuation neglect: ignoring deviations from average
- Molecular field: effective field from all neighbors
- Landau theory: expansion around the transition

When epistemic mean field IS present:
- Complex interactions replaced by effective average
- Field self-consistently determined
- Clear order parameter measurable
- Critical point where approximation fails
- Deviations from average being neglected
- Effective field from collective behavior
- Expansion around transition point

When full interaction is present:
- All interactions treated individually
- No self-consistent averaging
- No single order parameter
- No critical breakdown point
- All fluctuations included
- No effective field approximation
- No expansion needed

Output JSON with: mean_field_present (bool), severity (none/mild/moderate/severe), self_consistency (what circular determination), order_parameter (what measures order), critical_temperature (what breakdown point), fluctuation_neglect (what ignored deviations), recommendation (full_interaction/mild_mean_field/significant_mean_field/major_averaging/include_fluctuations)."""

EPISTEMIC_MEAN_FIELD_PROMPT = """Detect epistemic mean field:

Self-consistency: {self_consistency}
Order parameter: {order_parameter}
Critical temperature: {critical_temperature}
Fluctuation neglect: {fluctuation_neglect}
Domain: {domain}
Context: {context}

Are complex many-body intellectual interactions being replaced by an effective average field? Return ONLY valid JSON."""


class EpistemicMeanFieldService:
    """Detects epistemic mean field — replacing complex interactions with average field."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_consistency: str,
        *,
        order_parameter: str = "",
        critical_temperature: str = "",
        fluctuation_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mean field."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEAN_FIELD_PROMPT.format(
                self_consistency=self_consistency,
                order_parameter=order_parameter or "Not specified",
                critical_temperature=critical_temperature or "Not specified",
                fluctuation_neglect=fluctuation_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEAN_FIELD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_consistency": self_consistency[:200],
            "mean_field_present": data.get("mean_field_present", False),
            "severity": data.get("severity", ""),
            "order_parameter": data.get("order_parameter", ""),
            "critical_temperature": data.get("critical_temperature", ""),
            "fluctuation_neglect": data.get("fluctuation_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
