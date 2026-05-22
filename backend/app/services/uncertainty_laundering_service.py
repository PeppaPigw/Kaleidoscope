"""UncertaintyLaunderingService — Uncertainty Laundering Detection.

Detects uncertainty laundering — when uncertain inputs produce
falsely certain outputs through modeling, aggregation, or
transformation that hides the underlying uncertainty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNCERTAINTY_LAUNDERING_SYSTEM = """You are an uncertainty laundering specialist. Given a model or analysis, assess whether uncertainty is being hidden through processing:

Key concepts:
- Uncertainty laundering: uncertain inputs producing certain-looking outputs
- Precision washing: vague inputs transformed into precise numbers
- Model opacity: complexity hiding uncertainty from users
- Aggregation hiding: combining uncertain estimates to appear certain
- Confidence inflation: each processing step inflating apparent confidence
- Black box certainty: model producing confident outputs from uncertain inputs
- Uncertainty propagation failure: not tracking how uncertainty flows through

When uncertainty laundering IS present:
- Uncertain inputs producing falsely certain outputs
- Model hiding uncertainty from decision-makers
- Aggregation creating false precision
- Processing steps inflating apparent confidence
- Uncertainty not propagated through calculations
- Vague inputs transformed into precise-looking numbers
- Decision-makers unaware of underlying uncertainty

When uncertainty is properly handled:
- Uncertainty propagated through all calculations
- Output uncertainty reflects input uncertainty
- Confidence intervals provided with estimates
- Model limitations communicated to users
- Aggregation preserves uncertainty information
- Decision-makers aware of underlying uncertainty
- Sensitivity analysis performed

Output JSON with: laundering_present (bool), severity (none/mild/moderate/severe), model (what model or process), input_uncertainty (how uncertain inputs are), output_certainty (how certain outputs appear), mechanism (how uncertainty is hidden), recommendation (uncertainty_preserved/mild_precision_inflation/significant_laundering/major_certainty_fabrication/propagate_uncertainty)."""

UNCERTAINTY_LAUNDERING_PROMPT = """Detect uncertainty laundering:

Model: {model}
Inputs: {inputs}
Outputs: {outputs}
Uncertainty handling: {uncertainty}
Domain: {domain}
Context: {context}

Are uncertain inputs producing falsely certain outputs? Return ONLY valid JSON."""


class UncertaintyLaunderingService:
    """Detects uncertainty laundering — hiding uncertainty through processing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        model: str,
        *,
        inputs: str = "",
        outputs: str = "",
        uncertainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect uncertainty laundering."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNCERTAINTY_LAUNDERING_PROMPT.format(
                model=model,
                inputs=inputs or "Not specified",
                outputs=outputs or "Not specified",
                uncertainty=uncertainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNCERTAINTY_LAUNDERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "model": model[:200],
            "laundering_present": data.get("laundering_present", False),
            "severity": data.get("severity", ""),
            "input_uncertainty": data.get("input_uncertainty", ""),
            "output_certainty": data.get("output_certainty", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
