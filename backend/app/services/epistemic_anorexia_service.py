"""EpistemicAnorexiaService — Epistemic Anorexia Detection.

Detects epistemic anorexia — refusing to take in new information
despite genuine need, starving oneself of needed knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANOREXIA_SYSTEM = """You are an epistemic anorexia specialist. Given a knowledge-seeking pattern, assess whether new information is being refused despite genuine need:

Key concepts:
- Epistemic anorexia: refusing new information despite need
- Knowledge refusal: refusing needed knowledge
- Information avoidance: avoiding information that is needed
- Learning resistance: resisting learning despite need
- Update refusal: refusing to update despite new evidence
- Intellectual starvation: starving self of needed knowledge
- Closed mind: mind closed to needed new information

When epistemic anorexia IS present:
- New information refused despite genuine need
- Needed knowledge actively avoided
- Information that would help is rejected
- Learning resisted despite clear need
- Updates refused despite compelling evidence
- Self starved of needed knowledge
- Mind closed to information that would help

When appropriate selectivity is present:
- Information filtered appropriately
- Knowledge sought proportionate to need
- Information selected based on relevance
- Learning focused on genuine priorities
- Updates accepted when warranted
- Knowledge consumption appropriate to capacity
- Mind open to relevant new information

Output JSON with: anorexia_present (bool), severity (none/mild/moderate/severe), pattern (what refusal pattern exists), refused_information (what information is refused), genuine_need (what need exists), reason (why information is refused), recommendation (appropriate_selectivity/mild_avoidance/significant_epistemic_anorexia/major_knowledge_refusal/accept_needed_information)."""

EPISTEMIC_ANOREXIA_PROMPT = """Detect epistemic anorexia:

Pattern: {pattern}
Refused information: {refused}
Genuine need: {need}
Reason for refusal: {reason}
Domain: {domain}
Context: {context}

Is new information being refused despite genuine need? Return ONLY valid JSON."""


class EpistemicAnorexiaService:
    """Detects epistemic anorexia — refusing new information despite need."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        refused: str = "",
        need: str = "",
        reason: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anorexia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANOREXIA_PROMPT.format(
                pattern=pattern,
                refused=refused or "Not specified",
                need=need or "Not specified",
                reason=reason or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANOREXIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "anorexia_present": data.get("anorexia_present", False),
            "severity": data.get("severity", ""),
            "refused_information": data.get("refused_information", ""),
            "genuine_need": data.get("genuine_need", ""),
            "reason": data.get("reason", ""),
            "recommendation": data.get("recommendation", ""),
        }
