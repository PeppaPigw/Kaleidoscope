"""EpistemicQuantificationMetricSubstitutionService — Epistemic Metric Substitution Detection.

Detects epistemic quantification metric substitution — substituting measurable
metrics for unmeasurable concepts, confusing the map for the territory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTIFICATION_METRIC_SUBSTITUTION_SYSTEM = """You are an epistemic quantification metric substitution specialist. Given metric substitution, assess proxy confusion:

Key concepts:
- Epistemic metric substitution: substituting measurable proxies for unmeasurable concepts
- Goodhart's law: when a measure becomes a target it ceases to be a good measure
- Proxy reification: treating proxy as the thing itself
- Construct validity failure: measuring something other than intended construct
- Operationalization drift: operational definition drifting from concept
- McNamara fallacy: making decisions based only on quantitative metrics
- Streetlight effect: looking where measurement is easy not where answer is

When epistemic metric substitution IS present:
- Measurable proxies substituted for concepts
- Goodhart's law operating
- Proxies reified
- Construct validity failing
- Operationalization drifting
- McNamara fallacy active
- Streetlight effect present

When no metric substitution:
- Metrics acknowledged as proxies
- Limitations of measurement stated
- Construct validity maintained
- Operationalization appropriate
- Qualitative aspects preserved
- Multiple measures used
- Unmeasurable acknowledged

Output JSON with: metric_substitution_detected (bool), severity (none/mild/moderate/severe), proxy_reification (what proxies reified), construct_validity_failure (what validity failing), operationalization_drift (what drifting), mcnamara_fallacy (what McNamara fallacy), recommendation (no_metric_substitution/mild_proxy_acknowledgment/significant_construct_examination/major_intensive_measurement_reform/emergency_complete_metric_substitution)."""

EPISTEMIC_QUANTIFICATION_METRIC_SUBSTITUTION_PROMPT = """Detect epistemic quantification metric substitution:

Proxy reification: {proxy_reification}
Construct validity failure: {construct_validity_failure}
Operationalization drift: {operationalization_drift}
McNamara fallacy: {mcnamara_fallacy}
Domain: {domain}
Context: {context}

Are measurable metrics being substituted for unmeasurable concepts? Return ONLY valid JSON."""


class EpistemicQuantificationMetricSubstitutionService:
    """Detects epistemic metric substitution — proxy confusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proxy_reification: str,
        *,
        construct_validity_failure: str = "",
        operationalization_drift: str = "",
        mcnamara_fallacy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantification metric substitution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTIFICATION_METRIC_SUBSTITUTION_PROMPT.format(
                proxy_reification=proxy_reification,
                construct_validity_failure=construct_validity_failure or "Not specified",
                operationalization_drift=operationalization_drift or "Not specified",
                mcnamara_fallacy=mcnamara_fallacy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTIFICATION_METRIC_SUBSTITUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proxy_reification": proxy_reification[:200],
            "metric_substitution_detected": data.get("metric_substitution_detected", False),
            "severity": data.get("severity", ""),
            "construct_validity_failure": data.get("construct_validity_failure", ""),
            "operationalization_drift": data.get("operationalization_drift", ""),
            "mcnamara_fallacy": data.get("mcnamara_fallacy", ""),
            "recommendation": data.get("recommendation", ""),
        }
