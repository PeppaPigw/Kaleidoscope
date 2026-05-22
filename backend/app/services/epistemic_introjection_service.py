"""EpistemicIntrojectionService — Epistemic Introjection Detection.

Detects epistemic introjection — unconsciously incorporating another's
intellectual beliefs, values, or standards as one's own without critical examination.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTROJECTION_SYSTEM = """You are an epistemic introjection specialist. Given incorporated beliefs without examination, assess introjection:

Key concepts:
- Epistemic introjection: swallowing whole without digesting
- Uncritical incorporation: taking in without examination
- Foreign body: internalized material that doesn't fit
- Authority swallowing: absorbing authority's views wholesale
- Pseudo-conviction: feeling certain about unexamined beliefs
- Intellectual indigestion: discomfort from unprocessed material
- Identity colonization: other's beliefs replacing own

When epistemic introjection IS present:
- Swallowing without digesting
- Taking in without examination
- Internalized material doesn't fit
- Absorbing views wholesale
- Certain about unexamined beliefs
- Discomfort from unprocessed material
- Other's beliefs replacing own

When no introjection:
- Critical examination before accepting
- Thoughtful integration
- Beliefs fit coherently
- Selective adoption
- Examined convictions
- Processed and integrated
- Own beliefs maintained

Output JSON with: introjection_detected (bool), severity (none/mild/moderate/severe), incorporation_source (what swallowed), foreign_body (what doesn't fit), pseudo_conviction (what unexamined certainty), colonization_level (what replaced), recommendation (no_introjection/mild_examination_practice/significant_belief_audit/major_intensive_differentiation/emergency_identity_loss)."""

EPISTEMIC_INTROJECTION_PROMPT = """Detect epistemic introjection:

Incorporation source: {incorporation_source}
Foreign body: {foreign_body}
Pseudo conviction: {pseudo_conviction}
Colonization level: {colonization_level}
Domain: {domain}
Context: {context}

Is there unconscious incorporation of another's beliefs without critical examination? Return ONLY valid JSON."""


class EpistemicIntrojectionService:
    """Detects epistemic introjection — swallowing beliefs without examination."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        incorporation_source: str,
        *,
        foreign_body: str = "",
        pseudo_conviction: str = "",
        colonization_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic introjection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTROJECTION_PROMPT.format(
                incorporation_source=incorporation_source,
                foreign_body=foreign_body or "Not specified",
                pseudo_conviction=pseudo_conviction or "Not specified",
                colonization_level=colonization_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTROJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "incorporation_source": incorporation_source[:200],
            "introjection_detected": data.get("introjection_detected", False),
            "severity": data.get("severity", ""),
            "foreign_body": data.get("foreign_body", ""),
            "pseudo_conviction": data.get("pseudo_conviction", ""),
            "colonization_level": data.get("colonization_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
