"""EpistemicAnalogyOverextensionService — Epistemic Analogy Overextension Detection.

Detects epistemic analogy overextension — extending an analogy beyond
its valid domain where the mapping breaks down.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_OVEREXTENSION_SYSTEM = """You are an epistemic analogy overextension specialist. Given analogies extended beyond valid domains, assess overextension:

Key concepts:
- Epistemic analogy overextension: extending analogy beyond its valid domain
- Domain boundary violation: pushing analogy past where it applies
- Mapping breakdown: the mapping between source and target breaks down
- Diminishing returns: analogy becomes less useful as extended further
- False prediction: overextended analogy generates false predictions
- Explanatory overreach: analogy explains more than it should
- Metaphor creep: metaphor gradually takes over literal understanding

When epistemic analogy overextension IS present:
- Analogy extended too far
- Domain boundaries violated
- Mapping breaking down
- Returns diminishing
- False predictions generated
- Explanatory overreach occurring
- Metaphor creeping beyond bounds

When no overextension:
- Analogy used within valid bounds
- Domain boundaries respected
- Mapping holds
- Returns still positive
- Predictions accurate
- Explanation proportionate
- Metaphor bounded appropriately

Output JSON with: analogy_overextension_detected (bool), severity (none/mild/moderate/severe), domain_boundary_violation (what boundaries violated), mapping_breakdown (where mapping breaks), false_prediction (what false predictions), explanatory_overreach (what overreach), recommendation (no_analogy_overextension/mild_boundary_awareness/significant_domain_limiting/major_intensive_analogy_bounding/emergency_complete_overextension)."""

EPISTEMIC_ANALOGY_OVEREXTENSION_PROMPT = """Detect epistemic analogy overextension:

Domain boundary violation: {domain_boundary_violation}
Mapping breakdown: {mapping_breakdown}
False prediction: {false_prediction}
Explanatory overreach: {explanatory_overreach}
Domain: {domain}
Context: {context}

Is an analogy being extended beyond its valid domain? Return ONLY valid JSON."""


class EpistemicAnalogyOverextensionService:
    """Detects epistemic analogy overextension — analogy beyond valid bounds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domain_boundary_violation: str,
        *,
        mapping_breakdown: str = "",
        false_prediction: str = "",
        explanatory_overreach: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy overextension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_OVEREXTENSION_PROMPT.format(
                domain_boundary_violation=domain_boundary_violation,
                mapping_breakdown=mapping_breakdown or "Not specified",
                false_prediction=false_prediction or "Not specified",
                explanatory_overreach=explanatory_overreach or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_OVEREXTENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domain_boundary_violation": domain_boundary_violation[:200],
            "analogy_overextension_detected": data.get("analogy_overextension_detected", False),
            "severity": data.get("severity", ""),
            "mapping_breakdown": data.get("mapping_breakdown", ""),
            "false_prediction": data.get("false_prediction", ""),
            "explanatory_overreach": data.get("explanatory_overreach", ""),
            "recommendation": data.get("recommendation", ""),
        }
