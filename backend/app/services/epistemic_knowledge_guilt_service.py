"""EpistemicKnowledgeGuiltService — Epistemic Knowledge Guilt Detection.

Detects epistemic knowledge guilt — guilt over knowing things that
burden, isolate, or create responsibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KNOWLEDGE_GUILT_SYSTEM = """You are an epistemic knowledge guilt specialist. Given guilt over burdensome knowledge, assess knowledge guilt:

Key concepts:
- Epistemic knowledge guilt: guilt over knowing burdensome things
- Burden of knowledge: feeling weighed down by what one knows
- Isolation through knowing: knowledge separating from others
- Responsibility weight: feeling obligated to act on knowledge
- Cassandra guilt: knowing but being unable to convince others
- Complicit knowing: knowledge making one feel complicit
- Ignorance envy: wishing one didn't know

When epistemic knowledge guilt IS present:
- Guilt over knowing burdensome things
- Feeling weighed down
- Knowledge separating from others
- Feeling obligated to act
- Knowing but unable to convince
- Knowledge making complicit
- Wishing didn't know

When no knowledge guilt:
- Knowledge as empowering
- Carrying knowledge lightly
- Knowledge connecting to others
- Comfortable with responsibility
- Patient with communication
- Knowledge as neutral
- Grateful for understanding

Output JSON with: knowledge_guilt_detected (bool), severity (none/mild/moderate/severe), burden_of_knowledge (what weighed down by), isolation_through_knowing (what separating), responsibility_weight (what obligated about), cassandra_guilt (what unable to convince about), recommendation (no_knowledge_guilt/mild_burden_sharing/significant_responsibility_processing/major_intensive_guilt_work/emergency_paralyzing_knowledge_burden)."""

EPISTEMIC_KNOWLEDGE_GUILT_PROMPT = """Detect epistemic knowledge guilt:

Burden of knowledge: {burden_of_knowledge}
Isolation through knowing: {isolation_through_knowing}
Responsibility weight: {responsibility_weight}
Cassandra guilt: {cassandra_guilt}
Domain: {domain}
Context: {context}

Is there guilt over knowing things that burden or isolate? Return ONLY valid JSON."""


class EpistemicKnowledgeGuiltService:
    """Detects epistemic knowledge guilt — guilt over burdensome knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        burden_of_knowledge: str,
        *,
        isolation_through_knowing: str = "",
        responsibility_weight: str = "",
        cassandra_guilt: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic knowledge guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KNOWLEDGE_GUILT_PROMPT.format(
                burden_of_knowledge=burden_of_knowledge,
                isolation_through_knowing=isolation_through_knowing or "Not specified",
                responsibility_weight=responsibility_weight or "Not specified",
                cassandra_guilt=cassandra_guilt or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KNOWLEDGE_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "burden_of_knowledge": burden_of_knowledge[:200],
            "knowledge_guilt_detected": data.get("knowledge_guilt_detected", False),
            "severity": data.get("severity", ""),
            "isolation_through_knowing": data.get("isolation_through_knowing", ""),
            "responsibility_weight": data.get("responsibility_weight", ""),
            "cassandra_guilt": data.get("cassandra_guilt", ""),
            "recommendation": data.get("recommendation", ""),
        }
