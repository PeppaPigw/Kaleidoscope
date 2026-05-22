"""RhymeAsReasonService — Rhyme-as-Reason Effect Detection.

Detects the rhyme-as-reason effect (Eaton effect) — statements
that rhyme are perceived as more truthful, accurate, or wise
than equivalent non-rhyming statements. McGlone & Tofighbakhsh
(2000). "If the glove doesn't fit, you must acquit." Phonetic
fluency creates an illusion of truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RHYME_SYSTEM = """You are a rhyme-as-reason effect specialist. Given a statement or argument, assess whether phonetic fluency (rhyme, alliteration, rhythm) is creating an illusion of truth or wisdom:

Key concepts (McGlone & Tofighbakhsh, 2000):
- Rhyme-as-reason: rhyming statements perceived as more truthful
- Processing fluency: easy-to-process statements feel more true
- Keats heuristic: "beauty is truth" — aesthetic appeal = credibility
- Aphorism effect: pithy sayings feel wise regardless of content
- Alliteration bias: alliterative phrases feel more memorable and true
- Slogan effect: catchy phrasing substitutes for evidence

When the rhyme-as-reason effect IS present:
- A rhyming statement is being treated as evidence or proof
- Catchiness is substituting for logical argument
- "It rhymes, so it must be true" (often unconscious)
- Slogans or aphorisms used as if they were arguments
- Phonetic fluency creating false sense of wisdom
- Memorable phrasing given more weight than it deserves

When fluent language IS appropriate:
- The statement is independently verifiable and happens to rhyme
- The rhyme is used as a mnemonic, not as evidence
- The content is true regardless of its phonetic properties
- The speaker acknowledges the rhyme is for memorability, not proof
- The audience evaluates the content separately from the form

Output JSON with: rhyme_effect_present (bool), severity (none/mild/moderate/severe), statement (the fluent/rhyming statement), fluency_type (rhyme/alliteration/rhythm/meter/assonance), content_truth (is the content independently true?), fluency_as_evidence (bool — is the fluency being used as proof?), equivalent_non_rhyming (what would the same claim sound like without fluency?), persuasive_boost (how much extra credibility does the fluency add?), context_of_use (is it used as argument, mnemonic, or decoration?), audience_vulnerability (how susceptible is the audience?), logical_content (what is the actual logical claim?), evidence_independent (bool — is there evidence beyond the phrasing?), recommendation (content_valid/mild_fluency_bias/significant_rhyme_effect/major_fluency_substitution/evaluate_content_not_form)."""

RHYME_PROMPT = """Detect rhyme-as-reason effect:

Statement: {statement}
Context of use: {usage}
Audience: {audience}
Evidence provided: {evidence}
Domain: {domain}
Context: {context}

Is phonetic fluency creating an illusion of truth? Return ONLY valid JSON."""


class RhymeAsReasonService:
    """Detects rhyme-as-reason effect — phonetic fluency creating illusion of truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        usage: str = "",
        audience: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect rhyme-as-reason effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RHYME_PROMPT.format(
                statement=statement,
                usage=usage or "Not specified",
                audience=audience or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RHYME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "rhyme_effect_present": data.get("rhyme_effect_present", False),
            "severity": data.get("severity", ""),
            "fluency_type": data.get("fluency_type", ""),
            "content_truth": data.get("content_truth", ""),
            "fluency_as_evidence": data.get("fluency_as_evidence", False),
            "equivalent_non_rhyming": data.get("equivalent_non_rhyming", ""),
            "persuasive_boost": data.get("persuasive_boost", ""),
            "context_of_use": data.get("context_of_use", ""),
            "audience_vulnerability": data.get("audience_vulnerability", ""),
            "logical_content": data.get("logical_content", ""),
            "evidence_independent": data.get("evidence_independent", False),
            "recommendation": data.get("recommendation", ""),
        }
