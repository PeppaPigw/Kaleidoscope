"""StrategicEquivocationService — Strategic Equivocation Detection.

Detects strategic equivocation — deliberately using ambiguous terms
to mislead, where the same word is used with different meanings
to create false impressions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_EQUIVOCATION_SYSTEM = """You are a strategic equivocation specialist. Given a discourse, assess whether ambiguous terms are being deliberately used to mislead:

Key concepts:
- Strategic equivocation: deliberate ambiguity to mislead
- Meaning shifting: same term used with different meanings
- Deliberate ambiguity: ambiguity serving deception
- Equivocation as strategy: shifting meaning for advantage
- Definition gaming: exploiting multiple definitions
- Semantic manipulation: manipulating meaning for effect
- Plausible interpretation: maintaining multiple interpretations strategically

When strategic equivocation IS present:
- Terms deliberately used with shifting meanings
- Ambiguity serving deception or manipulation
- Same word meaning different things in different parts
- Definition exploited for rhetorical advantage
- Meaning shifted to avoid accountability
- Multiple interpretations maintained strategically
- Semantic manipulation creating false impressions

When appropriate nuance is present:
- Terms used consistently within context
- Ambiguity acknowledged and clarified
- Multiple meanings distinguished not exploited
- Definitions stable within argument
- Meaning consistent and transparent
- Nuance serving understanding not manipulation
- Interpretive range honest not strategic

Output JSON with: equivocation_present (bool), severity (none/mild/moderate/severe), discourse (what discourse occurs), term (what term is equivocated), meanings (what different meanings are used), strategy (how equivocation serves goals), recommendation (consistent_usage/mild_ambiguity/significant_strategic_equivocation/major_semantic_manipulation/use_terms_consistently)."""

STRATEGIC_EQUIVOCATION_PROMPT = """Detect strategic equivocation:

Discourse: {discourse}
Ambiguous term: {term}
Usage pattern: {usage}
Effect: {effect}
Domain: {domain}
Context: {context}

Are ambiguous terms being deliberately used to mislead? Return ONLY valid JSON."""


class StrategicEquivocationService:
    """Detects strategic equivocation — deliberate ambiguity to mislead."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        term: str = "",
        usage: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic equivocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_EQUIVOCATION_PROMPT.format(
                discourse=discourse,
                term=term or "Not specified",
                usage=usage or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_EQUIVOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "equivocation_present": data.get("equivocation_present", False),
            "severity": data.get("severity", ""),
            "term": data.get("term", ""),
            "meanings": data.get("meanings", ""),
            "strategy": data.get("strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }
