"""ArgumentFromSilenceService — Argument from Silence Detection.

Detects argument from silence — concluding that something is true
or false because no one has argued against or for it. Absence of
evidence is treated as evidence of absence (or presence).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARGUMENT_SILENCE_SYSTEM = """You are an argument from silence specialist. Given an argument, assess whether it draws conclusions from the absence of counter-arguments or evidence:

Key concepts:
- Argument from silence: absence of argument treated as evidence
- Absence of evidence vs evidence of absence: different things
- Negative evidence: when absence IS informative
- Publication bias: absence may reflect bias, not truth
- Chilling effect: silence may reflect suppression, not agreement
- Consensus by default: assuming agreement from lack of objection
- Burden of proof: who must speak up?

When argument from silence IS fallacious:
- "No one has disproved X, therefore X is true"
- Treating lack of objection as agreement
- "If it were wrong, someone would have said so"
- Assuming silence means there's nothing to say
- Ignoring reasons why people might not speak up
- "No evidence against" treated as "evidence for"
- Confusing absence of research with negative results

When silence IS informative:
- Thorough search has been conducted and nothing found
- The absence is surprising given what we'd expect if the claim were true
- Multiple independent sources have been checked
- The silence is in a domain where evidence would be expected
- Absence of side effects after extensive testing
- The claim predicts observable evidence that hasn't appeared
- The silence is from sources that would have reason to speak

Output JSON with: argument_from_silence_present (bool), severity (none/mild/moderate/severe), conclusion (what is concluded), silence (what silence is cited), search_thoroughness (how thorough was the search), expected_evidence (would we expect evidence if claim were true), alternative_explanations (why might there be silence), recommendation (silence_informative/mild_overinterpretation/significant_argument_from_silence/major_absence_as_evidence/distinguish_absence_types)."""

ARGUMENT_SILENCE_PROMPT = """Detect argument from silence:

Argument: {argument}
Silence cited: {silence}
Search conducted: {search}
Expected evidence: {expected}
Domain: {domain}
Context: {context}

Is this argument drawing conclusions from the absence of counter-arguments or evidence? Return ONLY valid JSON."""


class ArgumentFromSilenceService:
    """Detects argument from silence — conclusions drawn from absence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        silence: str = "",
        search: str = "",
        expected: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect argument from silence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARGUMENT_SILENCE_PROMPT.format(
                argument=argument,
                silence=silence or "Not specified",
                search=search or "Not specified",
                expected=expected or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ARGUMENT_SILENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "argument_from_silence_present": data.get("argument_from_silence_present", False),
            "severity": data.get("severity", ""),
            "search_thoroughness": data.get("search_thoroughness", ""),
            "expected_evidence": data.get("expected_evidence", ""),
            "alternative_explanations": data.get("alternative_explanations", ""),
            "recommendation": data.get("recommendation", ""),
        }
