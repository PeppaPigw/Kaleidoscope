"""CredibilityDeficitService — Credibility Deficit Detection.

Detects credibility deficit — systematic under-crediting of certain
sources based on identity rather than evidence quality, where
prejudice determines who is believed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDIBILITY_DEFICIT_SYSTEM = """You are a credibility deficit specialist. Given a credibility assessment, determine whether certain sources are systematically under-credited:

Key concepts:
- Credibility deficit: systematic under-crediting based on identity
- Testimonial injustice: prejudice reducing credibility
- Identity-based discounting: who you are determining belief
- Systematic under-crediting: pattern of reduced credibility
- Prejudicial credibility: prejudice shaping who is believed
- Source discounting: sources discounted for non-epistemic reasons
- Credibility gap: gap between actual and attributed credibility

When credibility deficit IS present:
- Sources systematically under-credited based on identity
- Prejudice reducing credibility assessments
- Who is speaking determining belief more than what is said
- Pattern of reduced credibility for certain groups
- Non-epistemic factors driving credibility judgments
- Sources discounted for reasons unrelated to evidence quality
- Gap between actual reliability and attributed credibility

When differential credibility is appropriate:
- Credibility based on track record and expertise
- Assessment based on evidence quality not source identity
- Differential credibility justified by relevant differences
- Who is speaking relevant only when expertise matters
- Credibility proportionate to demonstrated reliability
- Assessment based on epistemic rather than social factors
- Credibility gap explained by relevant factors

Output JSON with: deficit_present (bool), severity (none/mild/moderate/severe), assessment (what credibility assessment), source (who is under-credited), basis (what basis for deficit), pattern (what pattern exists), recommendation (appropriate_credibility/mild_identity_discounting/significant_credibility_deficit/major_testimonial_injustice/assess_credibility_by_evidence_not_identity)."""

CREDIBILITY_DEFICIT_PROMPT = """Detect credibility deficit:

Credibility assessment: {assessment}
Source under-credited: {source}
Basis for discounting: {basis}
Pattern observed: {pattern}
Domain: {domain}
Context: {context}

Are certain sources systematically under-credited based on identity rather than evidence quality? Return ONLY valid JSON."""


class CredibilityDeficitService:
    """Detects credibility deficit — systematic under-crediting based on identity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        source: str = "",
        basis: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect credibility deficit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDIBILITY_DEFICIT_PROMPT.format(
                assessment=assessment,
                source=source or "Not specified",
                basis=basis or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CREDIBILITY_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "deficit_present": data.get("deficit_present", False),
            "severity": data.get("severity", ""),
            "source": data.get("source", ""),
            "basis": data.get("basis", ""),
            "pattern": data.get("pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
