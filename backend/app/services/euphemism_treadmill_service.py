"""EuphemismTreadmillService — Euphemism Treadmill Detection.

Detects the euphemism treadmill — when successive euphemisms
accumulate to progressively obscure reality. Each new euphemism
eventually acquires the negative connotations of the original
term, prompting yet another replacement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EUPHEMISM_TREADMILL_SYSTEM = """You are a euphemism treadmill specialist. Given language use, assess whether euphemisms are obscuring reality:

Key concepts:
- Euphemism treadmill: successive euphemisms each acquiring negative connotations
- Linguistic sanitization: making harsh realities sound acceptable
- Doublespeak: language that obscures, disguises, or reverses meaning
- Semantic bleaching: words losing their original force through overuse
- Concept laundering: making problematic ideas acceptable through renaming
- Dysphemism: the opposite — using harsh language to make things sound worse
- Clarity vs sensitivity: balancing honest language with appropriate tone

When euphemism treadmill IS present:
- Multiple layers of euphemism obscuring the underlying reality
- Original meaning lost behind sanitized language
- Euphemism used to avoid accountability or honest discussion
- Language designed to prevent clear thinking about the topic
- Successive renamings without addressing underlying issues
- Clarity sacrificed for comfort
- Important distinctions hidden by vague language

When euphemism treadmill is NOT present:
- Language is clear and direct while remaining appropriate
- Euphemisms used for genuine sensitivity, not obscuration
- Underlying reality remains accessible through the language
- Terminology changes reflect genuine conceptual shifts
- Language enables rather than prevents clear thinking
- Appropriate balance of directness and sensitivity
- Meaning is preserved despite polite phrasing

Output JSON with: treadmill_present (bool), severity (none/mild/moderate/severe), euphemism (the sanitized language), reality (what it obscures), layers (how many euphemistic layers exist), purpose (sensitivity vs obscuration), recommendation (appropriate_language/mild_sanitization/significant_obscuration/major_doublespeak/use_direct_language)."""

EUPHEMISM_TREADMILL_PROMPT = """Detect euphemism treadmill:

Language: {language}
Topic: {topic}
Original term: {original}
Current usage: {usage}
Domain: {domain}
Context: {context}

Are euphemisms obscuring reality rather than serving genuine sensitivity? Return ONLY valid JSON."""


class EuphemismTreadmillService:
    """Detects euphemism treadmill — successive euphemisms obscuring reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        language: str,
        *,
        topic: str = "",
        original: str = "",
        usage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect euphemism treadmill."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EUPHEMISM_TREADMILL_PROMPT.format(
                language=language,
                topic=topic or "Not specified",
                original=original or "Not specified",
                usage=usage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EUPHEMISM_TREADMILL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "language": language[:200],
            "treadmill_present": data.get("treadmill_present", False),
            "severity": data.get("severity", ""),
            "euphemism": data.get("euphemism", ""),
            "reality": data.get("reality", ""),
            "purpose": data.get("purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
