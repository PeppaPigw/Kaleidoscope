"""EffortHeuristicService — Effort Heuristic Detection.

Detects the effort heuristic — judging the quality or value of
something by how much effort went into it. Kruger et al. (2004).
A painting that took 100 hours "must" be better than one that
took 10 minutes. More effort = more value, regardless of actual
quality. Related to labor theory of value and IKEA effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EFFORT_SYSTEM = """You are an effort heuristic specialist. Given a quality or value judgment, assess whether effort is being used as a proxy for quality:

Key concepts (Kruger et al., 2004):
- Effort heuristic: judging quality by effort invested
- Labor theory of value: more work = more value (often wrong)
- Efficiency penalty: penalizing efficient solutions because they "look easy"
- Artisanal bias: handmade = better, even when machine-made is superior
- Visible effort: preferring solutions that show their work
- IKEA effect overlap: but effort heuristic is about judging others' effort

When the effort heuristic IS present:
- Valuing a slow, laborious solution over a quick, elegant one
- "They must not have tried hard enough" for efficient work
- Preferring handmade/artisanal when mass-produced is objectively better
- Judging a proposal by its length rather than its insight
- Penalizing someone for making something look easy
- "It can't be good if it only took an hour"

When effort IS a valid quality signal:
- The domain genuinely requires extensive work (research, craftsmanship)
- Effort correlates with thoroughness in this specific context
- The effort represents genuine exploration of the solution space
- Quick solutions in this domain are typically incomplete
- The effort reflects attention to detail that matters

Output JSON with: effort_heuristic_present (bool), severity (none/mild/moderate/severe), judgment (what quality assessment is being made), effort_observed (how much effort is perceived), actual_quality (what is the objective quality?), effort_quality_correlation (does effort actually predict quality here?), efficiency_penalty (bool — is efficiency being penalized?), visible_labor_preference (bool — is visible effort preferred over invisible skill?), artisanal_bias (bool — is handmade preferred regardless of quality?), output_vs_input (is the judgment based on output quality or input effort?), domain_relevance (does effort matter in this domain?), recommendation (effort_relevant/mild_effort_heuristic/significant_effort_bias/major_efficiency_penalty/judge_output_not_input)."""

EFFORT_PROMPT = """Detect effort heuristic:

Judgment: {judgment}
Effort observed: {effort}
Actual quality: {quality}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is effort being used as a proxy for quality? Return ONLY valid JSON."""


class EffortHeuristicService:
    """Detects effort heuristic — judging quality by effort invested."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        effort: str = "",
        quality: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect effort heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EFFORT_PROMPT.format(
                judgment=judgment,
                effort=effort or "Not specified",
                quality=quality or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EFFORT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "effort_heuristic_present": data.get("effort_heuristic_present", False),
            "severity": data.get("severity", ""),
            "effort_observed": data.get("effort_observed", ""),
            "actual_quality": data.get("actual_quality", ""),
            "effort_quality_correlation": data.get("effort_quality_correlation", ""),
            "efficiency_penalty": data.get("efficiency_penalty", False),
            "visible_labor_preference": data.get("visible_labor_preference", False),
            "artisanal_bias": data.get("artisanal_bias", False),
            "output_vs_input": data.get("output_vs_input", ""),
            "domain_relevance": data.get("domain_relevance", ""),
            "recommendation": data.get("recommendation", ""),
        }
