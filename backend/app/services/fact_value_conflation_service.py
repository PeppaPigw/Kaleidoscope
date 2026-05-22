"""FactValueConflationService — Fact-Value Conflation Detection.

Detects fact-value conflation — conflating factual claims with value
judgments, presenting values as if they were facts or treating facts
as if they settled value questions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FACT_VALUE_CONFLATION_SYSTEM = """You are a fact-value conflation specialist. Given a claim, assess whether facts and values are being inappropriately conflated:

Key concepts:
- Fact-value conflation: treating values as facts or vice versa
- Naturalistic fallacy: deriving ought from is
- Value smuggling: hiding values in factual language
- Fact as value: treating factual claims as settling value questions
- Objectivity theater: presenting values as objective facts
- Descriptive-normative confusion: confusing description with prescription
- Hidden normativity: normative content disguised as descriptive

When fact-value conflation IS present:
- Values presented as if they were factual claims
- Facts treated as if they settled value questions
- Normative content hidden in descriptive language
- Value judgments disguised as objective observations
- Factual claims used to smuggle in values
- Is-ought boundary crossed without acknowledgment
- Descriptive and normative claims not distinguished

When claims are appropriately bounded:
- Facts and values clearly distinguished
- Value judgments explicitly marked as such
- Factual claims bounded to empirical content
- Normative implications acknowledged separately
- Is-ought transitions explicitly justified
- Descriptive and normative clearly separated
- Both facts and values given appropriate treatment

Output JSON with: conflation_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), factual_content (what factual content exists), value_content (what value content exists), conflation_type (how they are conflated), recommendation (appropriate_distinction/mild_boundary_blur/significant_fact_value_conflation/major_value_as_fact/distinguish_facts_from_values)."""

FACT_VALUE_CONFLATION_PROMPT = """Detect fact-value conflation:

Claim: {claim}
Factual basis: {factual}
Value component: {value}
Presentation: {presentation}
Domain: {domain}
Context: {context}

Are facts and values being inappropriately conflated? Return ONLY valid JSON."""


class FactValueConflationService:
    """Detects fact-value conflation — conflating facts with value judgments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        factual: str = "",
        value: str = "",
        presentation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect fact-value conflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FACT_VALUE_CONFLATION_PROMPT.format(
                claim=claim,
                factual=factual or "Not specified",
                value=value or "Not specified",
                presentation=presentation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FACT_VALUE_CONFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "conflation_present": data.get("conflation_present", False),
            "severity": data.get("severity", ""),
            "factual_content": data.get("factual_content", ""),
            "value_content": data.get("value_content", ""),
            "conflation_type": data.get("conflation_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
