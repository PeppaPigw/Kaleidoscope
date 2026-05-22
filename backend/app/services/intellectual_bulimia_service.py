"""IntellectualBulimiaService — Intellectual Bulimia Detection.

Detects intellectual bulimia — binge-consuming then purging knowledge
without retention or integration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_BULIMIA_SYSTEM = """You are an intellectual bulimia specialist. Given a learning pattern, assess whether knowledge is being consumed and purged without retention:

Key concepts:
- Intellectual bulimia: binge-consuming then purging knowledge
- Cram and forget: cramming information then immediately forgetting
- Consumption without retention: consuming without retaining
- Learning cycle failure: learning cycle not completing
- Integration failure: knowledge not integrated into understanding
- Temporary knowledge: knowledge held only temporarily
- Purge after consumption: knowledge purged after use

When intellectual bulimia IS present:
- Knowledge binge-consumed then purged
- Information crammed then immediately forgotten
- Consumption occurring without retention
- Learning cycle not completing to integration
- Knowledge not integrated into understanding
- Knowledge held only temporarily for immediate use
- Purged after immediate purpose served

When healthy learning is present:
- Knowledge consumed and retained
- Information learned and integrated
- Consumption leading to lasting understanding
- Learning cycle completing to integration
- Knowledge becoming part of understanding
- Knowledge retained for long-term use
- Integration following consumption

Output JSON with: bulimia_present (bool), severity (none/mild/moderate/severe), pattern (what learning pattern exists), consumption (what is consumed), retention (what is retained), purge (what is purged), recommendation (healthy_learning/mild_retention_failure/significant_intellectual_bulimia/major_knowledge_purging/integrate_knowledge_durably)."""

INTELLECTUAL_BULIMIA_PROMPT = """Detect intellectual bulimia:

Learning pattern: {pattern}
Consumption: {consumption}
Retention: {retention}
Integration: {integration}
Domain: {domain}
Context: {context}

Is knowledge being consumed and purged without retention? Return ONLY valid JSON."""


class IntellectualBulimiaService:
    """Detects intellectual bulimia — binge-consuming then purging knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        consumption: str = "",
        retention: str = "",
        integration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual bulimia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_BULIMIA_PROMPT.format(
                pattern=pattern,
                consumption=consumption or "Not specified",
                retention=retention or "Not specified",
                integration=integration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_BULIMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "bulimia_present": data.get("bulimia_present", False),
            "severity": data.get("severity", ""),
            "consumption": data.get("consumption", ""),
            "retention": data.get("retention", ""),
            "purge": data.get("purge", ""),
            "recommendation": data.get("recommendation", ""),
        }
