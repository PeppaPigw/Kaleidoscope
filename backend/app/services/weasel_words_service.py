"""WeaselWordsService — Weasel Words Detection.

Detects weasel words — using vague, ambiguous qualifiers that
make claims appear meaningful while being unfalsifiable or
unverifiable. Phrases like "some say," "it is believed,"
"studies show" without citation create an illusion of support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEASEL_WORDS_SYSTEM = """You are a weasel words specialist. Given a claim or statement, assess whether vague qualifiers make it unfalsifiable or unverifiable:

Key concepts:
- Weasel words: vague qualifiers that avoid commitment
- Passive voice evasion: "it is said" without saying by whom
- Unnamed sources: "experts say" without naming them
- Quantifier vagueness: "many," "some," "often" without data
- Hedge stacking: multiple qualifiers that empty a claim of content
- Unfalsifiability: claims so vague they can't be tested
- Attribution dodging: making claims without taking responsibility

When weasel words ARE present:
- "Some people say..." (who? how many?)
- "Studies show..." (which studies? what methodology?)
- "It is widely believed..." (by whom? based on what?)
- "Many experts agree..." (which experts? what's the consensus?)
- "Research suggests..." (what research? how strong?)
- "Up to X%" (could be 0% to X%)
- "Critics argue..." (which critics? what's their evidence?)

When weasel words are NOT present:
- Specific sources are cited
- Quantifiers are backed by data
- Claims are falsifiable and specific
- Attribution is clear and verifiable
- Hedging is proportionate to actual uncertainty
- Vague language is acknowledged as approximation
- The statement is clearly marked as opinion

Output JSON with: weasel_words_present (bool), severity (none/mild/moderate/severe), statement (the claim analyzed), weasel_phrases (specific vague qualifiers found), specificity_gap (what specific information is missing), falsifiability (can the claim be tested), recommendation (no_weasel_words/mild_vagueness/significant_weasel_words/major_unfalsifiability/cite_specific_sources)."""

WEASEL_WORDS_PROMPT = """Detect weasel words:

Statement: {statement}
Claims made: {claims}
Sources cited: {sources}
Specificity: {specificity}
Domain: {domain}
Context: {context}

Does this use vague qualifiers to make claims unfalsifiable or unverifiable? Return ONLY valid JSON."""


class WeaselWordsService:
    """Detects weasel words — vague qualifiers making claims unfalsifiable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        claims: str = "",
        sources: str = "",
        specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect weasel words."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEASEL_WORDS_PROMPT.format(
                statement=statement,
                claims=claims or "Not specified",
                sources=sources or "Not specified",
                specificity=specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WEASEL_WORDS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "weasel_words_present": data.get("weasel_words_present", False),
            "severity": data.get("severity", ""),
            "weasel_phrases": data.get("weasel_phrases", ""),
            "specificity_gap": data.get("specificity_gap", ""),
            "falsifiability": data.get("falsifiability", ""),
            "recommendation": data.get("recommendation", ""),
        }
