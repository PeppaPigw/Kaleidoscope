"""NormalcyBiasService — Normalcy Bias Detection.

Detects normalcy bias — the tendency to underestimate the
probability and impact of disasters because "it's never happened
before" or "things have always been fine." People interpret
warning signs through the lens of normalcy, failing to prepare
for or respond to unprecedented events.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NORMALCY_SYSTEM = """You are a normalcy bias specialist. Given a risk assessment or response to warning signs, detect whether normalcy bias is preventing appropriate action:

Key concepts:
- "It can't happen here" / "It's never happened before"
- Interpreting warning signs as normal variation rather than signals
- Underweighting tail risks and black swans
- Creeping normality: gradual deterioration not noticed because each step is small
- Boiling frog: failing to react to slowly increasing danger
- Optimism bias overlap: believing bad things happen to others, not us

Assess:
- Are warning signs being dismissed or rationalized?
- Is historical normalcy being used to predict future safety?
- Is the base rate of the threat being underestimated?
- Are preparation costs being overweighted relative to potential losses?
- Is there a failure to update beliefs in response to new evidence?

Output JSON with: normalcy_bias_present (bool), severity (none/mild/moderate/severe/dangerous), warning_signs_present (list of warning signs being ignored), rationalization (how the signs are being explained away), historical_precedent (what "it's always been fine" is based on), base_rate_of_threat (actual probability of the bad outcome), perceived_probability (what people think the probability is), underestimation_factor (how much the risk is being underestimated), creeping_normality (bool — is gradual deterioration being missed?), preparation_cost (what it would cost to prepare), potential_loss (what could be lost if the threat materializes), cost_benefit_of_preparation (rational analysis of preparing vs not), update_failure (what new evidence is being ignored), who_is_warning (who is raising alarms and being dismissed), historical_analogues (similar situations where normalcy bias led to disaster), time_to_potential_event (how soon the threat could materialize), recommendation (appropriate_calm/mild_underreaction/significant_bias/dangerous_complacency/immediate_action_needed)."""

NORMALCY_PROMPT = """Detect normalcy bias:

Situation: {situation}
Warning signs: {warnings}
Current response: {response}
Historical context: {history}
Domain: {domain}
Context: {context}

Is normalcy bias preventing appropriate action? Return ONLY valid JSON."""


class NormalcyBiasService:
    """Detects normalcy bias — underestimating unprecedented threats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        warnings: str = "",
        response: str = "",
        history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect normalcy bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NORMALCY_PROMPT.format(
                situation=situation,
                warnings=warnings or "Not specified",
                response=response or "Not specified",
                history=history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NORMALCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "normalcy_bias_present": data.get("normalcy_bias_present", False),
            "severity": data.get("severity", ""),
            "warning_signs_present": data.get("warning_signs_present", []),
            "rationalization": data.get("rationalization", ""),
            "historical_precedent": data.get("historical_precedent", ""),
            "base_rate_of_threat": data.get("base_rate_of_threat", ""),
            "perceived_probability": data.get("perceived_probability", ""),
            "underestimation_factor": data.get("underestimation_factor", ""),
            "creeping_normality": data.get("creeping_normality", False),
            "preparation_cost": data.get("preparation_cost", ""),
            "potential_loss": data.get("potential_loss", ""),
            "cost_benefit_of_preparation": data.get("cost_benefit_of_preparation", ""),
            "update_failure": data.get("update_failure", ""),
            "who_is_warning": data.get("who_is_warning", ""),
            "historical_analogues": data.get("historical_analogues", []),
            "time_to_potential_event": data.get("time_to_potential_event", ""),
            "recommendation": data.get("recommendation", ""),
        }
