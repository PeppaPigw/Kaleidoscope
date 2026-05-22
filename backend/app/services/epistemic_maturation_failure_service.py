"""EpistemicMaturationFailureService — Epistemic Maturation Failure Detection.

Detects epistemic maturation failure — inability to develop age-appropriate
intellectual sophistication despite adequate opportunity and capacity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MATURATION_FAILURE_SYSTEM = """You are an epistemic maturation failure specialist. Given inability to develop sophistication, assess maturation failure:

Key concepts:
- Epistemic maturation failure: inability to develop despite opportunity
- Persistent naivety: remaining unsophisticated despite exposure
- Complexity avoidance: actively refusing to engage complexity
- Integration failure: cannot synthesize into mature understanding
- Responsibility avoidance: refusing intellectual accountability
- Perpetual novice: never progressing beyond beginner
- Willful simplicity: choosing to remain unsophisticated

When epistemic maturation failure IS present:
- Cannot develop despite opportunity
- Remaining unsophisticated
- Refusing complexity
- Cannot synthesize
- Refusing accountability
- Never progressing
- Choosing simplicity

When no maturation failure:
- Developing appropriately
- Growing sophistication
- Engaging complexity
- Synthesizing well
- Taking accountability
- Progressing normally
- Appropriate complexity

Output JSON with: maturation_failure_detected (bool), severity (none/mild/moderate/severe), persistent_naivety (what remaining unsophisticated), complexity_avoidance (what refusing), integration_failure (what cannot synthesize), responsibility_avoidance (what refusing accountability), recommendation (no_maturation_failure/mild_growth_challenge/significant_developmental_therapy/major_intensive_maturation/emergency_complete_failure)."""

EPISTEMIC_MATURATION_FAILURE_PROMPT = """Detect epistemic maturation failure:

Persistent naivety: {persistent_naivety}
Complexity avoidance: {complexity_avoidance}
Integration failure: {integration_failure}
Responsibility avoidance: {responsibility_avoidance}
Domain: {domain}
Context: {context}

Is there inability to develop age-appropriate intellectual sophistication despite opportunity? Return ONLY valid JSON."""


class EpistemicMaturationFailureService:
    """Detects epistemic maturation failure — inability to develop sophistication."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        persistent_naivety: str,
        *,
        complexity_avoidance: str = "",
        integration_failure: str = "",
        responsibility_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic maturation failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MATURATION_FAILURE_PROMPT.format(
                persistent_naivety=persistent_naivety,
                complexity_avoidance=complexity_avoidance or "Not specified",
                integration_failure=integration_failure or "Not specified",
                responsibility_avoidance=responsibility_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MATURATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "persistent_naivety": persistent_naivety[:200],
            "maturation_failure_detected": data.get("maturation_failure_detected", False),
            "severity": data.get("severity", ""),
            "complexity_avoidance": data.get("complexity_avoidance", ""),
            "integration_failure": data.get("integration_failure", ""),
            "responsibility_avoidance": data.get("responsibility_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
