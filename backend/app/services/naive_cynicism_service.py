"""NaiveCynicismService — Naive Cynicism Detection.

Detects naive cynicism — assuming others are more selfishly
motivated than they actually are. Kruger & Gilovich (1999).
"They're only doing it for the money/power/status." Leads to
distrust, missed collaboration opportunities, and adversarial
framing of neutral situations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NAIVE_CYNICISM_SYSTEM = """You are a naive cynicism specialist. Given an attribution of others' motives, assess whether the person is assuming more selfish motivation than evidence supports:

Key concepts (Kruger & Gilovich, 1999):
- Naive cynicism: assuming others are more self-interested than they are
- Motive attribution asymmetry: seeing own motives as pure, others' as selfish
- Cynical attribution: defaulting to selfish explanations for others' behavior
- Trust deficit: assuming bad faith without evidence
- Projection of self-interest: assuming others think like a self-interested actor
- Hostile attribution bias overlap: assuming hostile intent
- Actor-observer asymmetry: charitable to self, cynical about others

When naive cynicism IS present:
- "They're only doing it for the money" without evidence
- Assuming hidden selfish motives behind apparently generous actions
- "What's in it for them?" as default response to others' behavior
- Dismissing altruistic explanations without considering them
- Assuming competitors/colleagues are always acting in bad faith
- "Nobody does anything for free" applied universally

When the cynicism IS warranted:
- There is specific evidence of selfish motivation
- Past behavior demonstrates a pattern of self-interest
- The situation has clear incentive structures that favor self-interest
- Multiple independent observers reach the same conclusion
- The person has considered charitable interpretations and found them lacking

Output JSON with: naive_cynicism_present (bool), severity (none/mild/moderate/severe), attribution (what motive is being attributed), target (whose motives are being assessed), evidence_for_cynicism (what evidence supports selfish motive?), evidence_against (what evidence supports non-selfish motive?), charitable_interpretation (what would a charitable reading be?), motive_asymmetry (bool — different standards for self vs others?), trust_impact (how does this affect relationships/collaboration?), pattern_or_assumption (is this based on pattern or default assumption?), recommendation (cynicism_warranted/mild_cynicism/significant_motive_distortion/major_naive_cynicism/consider_charitable_interpretation)."""

NAIVE_CYNICISM_PROMPT = """Detect naive cynicism:

Attribution: {attribution}
Target: {target}
Evidence: {evidence}
Relationship: {relationship}
Domain: {domain}
Context: {context}

Is the person assuming more selfish motivation than evidence supports? Return ONLY valid JSON."""


class NaiveCynicismService:
    """Detects naive cynicism — assuming others are more selfish than they are."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attribution: str,
        *,
        target: str = "",
        evidence: str = "",
        relationship: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect naive cynicism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NAIVE_CYNICISM_PROMPT.format(
                attribution=attribution,
                target=target or "Not specified",
                evidence=evidence or "Not specified",
                relationship=relationship or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NAIVE_CYNICISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attribution": attribution[:200],
            "naive_cynicism_present": data.get("naive_cynicism_present", False),
            "severity": data.get("severity", ""),
            "target": data.get("target", ""),
            "evidence_for_cynicism": data.get("evidence_for_cynicism", ""),
            "evidence_against": data.get("evidence_against", ""),
            "charitable_interpretation": data.get("charitable_interpretation", ""),
            "motive_asymmetry": data.get("motive_asymmetry", False),
            "trust_impact": data.get("trust_impact", ""),
            "pattern_or_assumption": data.get("pattern_or_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }
