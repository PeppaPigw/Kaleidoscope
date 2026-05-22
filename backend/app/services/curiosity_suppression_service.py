"""CuriositySuppressionService — Curiosity Suppression Detection.

Detects curiosity suppression — social, institutional, or
psychological mechanisms that actively discourage inquiry,
punish questioning, or make curiosity costly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CURIOSITY_SUPPRESSION_SYSTEM = """You are a curiosity suppression specialist. Given a knowledge environment, assess whether curiosity is being actively suppressed:

Key concepts:
- Curiosity suppression: actively discouraging inquiry
- Question punishment: penalizing those who ask
- Inquiry costs: making questioning expensive
- Institutional anti-curiosity: organizations discouraging questions
- Social pressure against inquiry: norms against questioning
- Curiosity as threat: treating questions as dangerous
- Knowledge contentment enforcement: requiring satisfaction with status quo

When curiosity suppression IS present:
- Questions actively discouraged or punished
- Inquiry made costly or dangerous
- Institutions penalize questioning
- Social norms suppress curiosity
- Questions treated as threats
- Contentment with current knowledge enforced
- Curiosity seen as insubordination

When focus is appropriate:
- Boundaries serve productive inquiry
- Questions channeled not suppressed
- Focus on relevant questions encouraged
- Curiosity directed not eliminated
- Questioning welcomed within appropriate scope
- Inquiry supported with resources
- Boundaries transparent and justified

Output JSON with: suppression_present (bool), severity (none/mild/moderate/severe), environment (what environment), mechanism (how curiosity is suppressed), cost (what cost is imposed), effect (what inquiry is lost), recommendation (appropriate_focus/mild_question_discouragement/significant_curiosity_suppression/major_inquiry_punishment/encourage_curiosity)."""

CURIOSITY_SUPPRESSION_PROMPT = """Detect curiosity suppression:

Environment: {environment}
Response to questions: {response}
Costs of inquiry: {costs}
Norms about questioning: {norms}
Domain: {domain}
Context: {context}

Is curiosity being actively suppressed through punishment or social pressure? Return ONLY valid JSON."""


class CuriositySuppressionService:
    """Detects curiosity suppression — actively discouraging inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        response: str = "",
        costs: str = "",
        norms: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curiosity suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CURIOSITY_SUPPRESSION_PROMPT.format(
                environment=environment,
                response=response or "Not specified",
                costs=costs or "Not specified",
                norms=norms or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CURIOSITY_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "suppression_present": data.get("suppression_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "cost": data.get("cost", ""),
            "effect": data.get("effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
