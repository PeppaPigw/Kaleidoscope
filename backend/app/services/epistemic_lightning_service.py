"""EpistemicLightningService — Epistemic Lightning Detection.

Detects epistemic lightning — sudden flashes of insight that may
be illusory or genuine, requiring careful evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LIGHTNING_SYSTEM = """You are an epistemic lightning specialist. Given an insight claim, assess whether a sudden flash of understanding is genuine or illusory:

Key concepts:
- Epistemic lightning: sudden flash of insight
- Illusory insight: insight that feels real but is false
- Genuine breakthrough: real sudden understanding
- Flash evaluation: evaluating sudden insights
- Eureka reliability: how reliable eureka moments are
- Pattern completion: brain completing patterns prematurely
- Insight validation: validating sudden insights

When epistemic lightning IS illusory:
- Sudden insight that feels compelling but is wrong
- Flash of understanding based on false pattern
- Eureka moment not supported by evidence
- Brain completing pattern prematurely
- Insight driven by desire rather than evidence
- Flash of certainty without justification
- Sudden understanding that doesn't survive scrutiny

When genuine insight is present:
- Sudden understanding that proves correct
- Flash of insight connecting real patterns
- Eureka moment supported by subsequent evidence
- Pattern completion reflecting genuine structure
- Insight driven by accumulated evidence
- Flash of certainty justified by reasoning
- Sudden understanding that survives scrutiny

Output JSON with: illusory_lightning_present (bool), severity (none/mild/moderate/severe), insight (what insight is claimed), evaluation (whether it appears genuine or illusory), evidence (what evidence supports or contradicts), reliability (how reliable the insight seems), recommendation (genuine_insight/mild_uncertainty/significant_illusory_risk/major_false_eureka/validate_before_acting)."""

EPISTEMIC_LIGHTNING_PROMPT = """Detect epistemic lightning:

Insight: {insight}
Evaluation: {evaluation}
Evidence: {evidence}
Reliability: {reliability}
Domain: {domain}
Context: {context}

Is this sudden flash of insight genuine or potentially illusory? Return ONLY valid JSON."""


class EpistemicLightningService:
    """Detects epistemic lightning — sudden insights that may be illusory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        insight: str,
        *,
        evaluation: str = "",
        evidence: str = "",
        reliability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lightning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LIGHTNING_PROMPT.format(
                insight=insight,
                evaluation=evaluation or "Not specified",
                evidence=evidence or "Not specified",
                reliability=reliability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LIGHTNING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "insight": insight[:200],
            "illusory_lightning_present": data.get("illusory_lightning_present", False),
            "severity": data.get("severity", ""),
            "evaluation": data.get("evaluation", ""),
            "evidence": data.get("evidence", ""),
            "reliability": data.get("reliability", ""),
            "recommendation": data.get("recommendation", ""),
        }
