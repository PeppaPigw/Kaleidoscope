"""WeaselAmplificationService — Weasel Amplification Detection.

Detects weasel amplification — when vague qualifiers, passive
voice, and attribution to unnamed sources are used to make
claims unfalsifiable while still creating strong impressions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEASEL_AMPLIFICATION_SYSTEM = """You are a weasel amplification specialist. Given a statement, assess whether vague qualifiers make claims unfalsifiable:

Key concepts:
- Weasel words: vague qualifiers that weaken claims while preserving impression
- Unfalsifiability: claims that can't be proven wrong due to vagueness
- Attribution laundering: "some say", "experts believe", "studies show"
- Passive voice evasion: hiding who is responsible or claiming
- Hedge stacking: multiple qualifiers creating plausible deniability
- Impression vs commitment: creating strong impressions without commitment
- Quantifier abuse: "many", "most", "significant" without specifics

When weasel amplification IS present:
- Vague qualifiers making claims unfalsifiable
- "Some experts say" without naming experts
- "Studies show" without citing studies
- "Many people believe" without quantification
- Passive voice hiding responsibility
- Multiple hedges creating plausible deniability
- Strong impression created with no falsifiable claim

When weasel amplification is NOT present:
- Claims are specific and falsifiable
- Sources are named and verifiable
- Qualifiers are precise ("3 of 5 studies")
- Active voice with clear attribution
- Hedges used appropriately for genuine uncertainty
- Impression matches the actual strength of the claim
- Claims can be checked and potentially refuted

Output JSON with: amplification_present (bool), severity (none/mild/moderate/severe), statement (what is being claimed), weasel_techniques (what vague qualifiers are used), falsifiability (can the claim be tested), impression_created (what impression is left), recommendation (clear_language/mild_vagueness/significant_weaseling/major_unfalsifiable_impression/make_specific_and_testable)."""

WEASEL_AMPLIFICATION_PROMPT = """Detect weasel amplification:

Statement: {statement}
Attribution: {attribution}
Qualifiers used: {qualifiers}
Specificity: {specificity}
Domain: {domain}
Context: {context}

Are vague qualifiers making this claim unfalsifiable while creating strong impressions? Return ONLY valid JSON."""


class WeaselAmplificationService:
    """Detects weasel amplification — vague qualifiers making claims unfalsifiable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        attribution: str = "",
        qualifiers: str = "",
        specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect weasel amplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEASEL_AMPLIFICATION_PROMPT.format(
                statement=statement,
                attribution=attribution or "Not specified",
                qualifiers=qualifiers or "Not specified",
                specificity=specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WEASEL_AMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "amplification_present": data.get("amplification_present", False),
            "severity": data.get("severity", ""),
            "weasel_techniques": data.get("weasel_techniques", ""),
            "falsifiability": data.get("falsifiability", ""),
            "impression_created": data.get("impression_created", ""),
            "recommendation": data.get("recommendation", ""),
        }
