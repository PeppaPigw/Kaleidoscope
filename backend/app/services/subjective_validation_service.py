"""SubjectiveValidationService — Subjective Validation / Barnum Effect Detection.

Detects subjective validation — accepting vague, general
statements as personally meaningful and accurate. Forer (1949).
The Barnum effect. Horoscopes, personality tests, cold reading
all exploit this. People find personal meaning in statements
that apply to almost everyone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SUBJECTIVE_VALIDATION_SYSTEM = """You are a subjective validation specialist. Given a statement being accepted as personally meaningful, assess whether it's genuinely specific or exploiting the Barnum effect:

Key concepts (Forer, 1949):
- Barnum effect: accepting vague statements as uniquely personal
- Subjective validation: personal meaning found in general statements
- Cold reading: using vague statements that seem specific
- Base rate of applicability: how many people would this apply to?
- Confirmation bias interaction: noticing hits, ignoring misses
- Personal validation: feeling understood by generic descriptions
- Flattery effect: accepting positive vague statements more readily

When subjective validation IS present:
- Accepting horoscope-like statements as personally insightful
- Finding deep meaning in personality test results that apply to everyone
- "That's so me!" for statements with 80%+ base rate applicability
- Feeling uniquely understood by generic advice or descriptions
- Accepting vague predictions as specific and accurate
- Cold reading techniques being accepted as genuine insight

When the statement IS genuinely specific:
- It makes falsifiable predictions about specific behaviors
- It would NOT apply to most people (low base rate)
- It references specific, verifiable details
- Independent verification confirms its accuracy
- It distinguishes the person from others in meaningful ways

Output JSON with: subjective_validation_present (bool), severity (none/mild/moderate/severe), statement (what statement is being accepted), specificity (how specific is the statement actually?), base_rate (what percentage of people would this apply to?), personal_meaning_assigned (what personal meaning is being found?), falsifiable (bool — does the statement make testable predictions?), flattery_component (bool — is the statement flattering?), source_credibility (what gives the source credibility?), recommendation (statement_genuinely_specific/mild_barnum/significant_subjective_validation/major_barnum_effect/test_specificity)."""

SUBJECTIVE_VALIDATION_PROMPT = """Detect subjective validation (Barnum effect):

Statement: {statement}
Acceptance: {acceptance}
Source: {source}
Specificity: {specificity}
Domain: {domain}
Context: {context}

Is the person finding personal meaning in a vague general statement? Return ONLY valid JSON."""


class SubjectiveValidationService:
    """Detects subjective validation — accepting vague statements as personally meaningful."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        acceptance: str = "",
        source: str = "",
        specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect subjective validation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SUBJECTIVE_VALIDATION_PROMPT.format(
                statement=statement,
                acceptance=acceptance or "Not specified",
                source=source or "Not specified",
                specificity=specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SUBJECTIVE_VALIDATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "subjective_validation_present": data.get("subjective_validation_present", False),
            "severity": data.get("severity", ""),
            "specificity": data.get("specificity", ""),
            "base_rate": data.get("base_rate", ""),
            "personal_meaning_assigned": data.get("personal_meaning_assigned", ""),
            "falsifiable": data.get("falsifiable", True),
            "flattery_component": data.get("flattery_component", False),
            "source_credibility": data.get("source_credibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
