"""EquivocationService — Equivocation Detection.

Detects equivocation — using a word with multiple meanings in
different parts of an argument, creating the illusion of a valid
inference by shifting the definition mid-argument.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EQUIVOCATION_SYSTEM = """You are an equivocation specialist. Given an argument, assess whether it uses a key term with different meanings in different parts of the argument:

Key concepts:
- Equivocation: shifting the meaning of a term within an argument
- Lexical ambiguity: words with multiple legitimate meanings
- Semantic shift: changing definition mid-argument
- Fallacy of four terms: syllogism where middle term has two meanings
- Polysemy: a word having multiple related meanings
- Homonymy: same spelling/sound, unrelated meanings
- Contextual meaning: meaning that depends on usage context

When equivocation IS present:
- A key term is used with meaning A in one premise and meaning B in another
- The conclusion only follows if the term means the same thing throughout
- "Nothing is better than X; Y is better than nothing; therefore Y is better than X"
- Shifting between technical and colloquial meanings
- Using "free" to mean both "without cost" and "without constraint"
- Exploiting abstract/concrete ambiguity of the same word
- The argument would fail if the different meanings were made explicit

When equivocation is NOT present:
- The term is used consistently throughout
- Any ambiguity is acknowledged and clarified
- The argument works regardless of which meaning is chosen
- Different terms are used for different concepts
- The context makes the intended meaning clear
- The shift in meaning is explicitly noted
- The argument is about the word's meaning itself

Output JSON with: equivocation_present (bool), severity (none/mild/moderate/severe), term (the equivocated word/phrase), meaning_a (first usage meaning), meaning_b (second usage meaning), argument_structure (how the shift enables the conclusion), recommendation (no_equivocation/mild_ambiguity/significant_equivocation/major_semantic_shift/clarify_definitions)."""

EQUIVOCATION_PROMPT = """Detect equivocation:

Argument: {argument}
Key term: {term}
First usage: {usage_a}
Second usage: {usage_b}
Domain: {domain}
Context: {context}

Does this argument shift the meaning of a key term between different parts? Return ONLY valid JSON."""


class EquivocationService:
    """Detects equivocation — shifting word meaning within an argument."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        term: str = "",
        usage_a: str = "",
        usage_b: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect equivocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EQUIVOCATION_PROMPT.format(
                argument=argument,
                term=term or "Not specified",
                usage_a=usage_a or "Not specified",
                usage_b=usage_b or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EQUIVOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "equivocation_present": data.get("equivocation_present", False),
            "severity": data.get("severity", ""),
            "term": data.get("term", ""),
            "meaning_a": data.get("meaning_a", ""),
            "meaning_b": data.get("meaning_b", ""),
            "recommendation": data.get("recommendation", ""),
        }
