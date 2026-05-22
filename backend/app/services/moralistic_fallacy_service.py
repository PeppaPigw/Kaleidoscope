"""MoralisticFallacyService — Moralistic Fallacy Detection.

Detects the moralistic fallacy — deriving 'is' from 'ought',
claiming something must be true because it would be morally
good if it were true.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORALISTIC_FALLACY_SYSTEM = """You are a moralistic fallacy specialist. Given an argument, assess whether factual claims are being derived from moral beliefs:

Key concepts:
- Moralistic fallacy: inferring 'is' from 'ought'
- Wishful thinking: believing what we want to be true
- Reverse naturalistic fallacy: values determining claimed facts
- Moral motivation of belief: believing facts because of values
- Ideological science: conclusions predetermined by ideology
- Taboo facts: denying facts because they're morally uncomfortable
- Ought-implies-is: moral desirability treated as evidence

When the moralistic fallacy IS present:
- Factual claims derived from moral preferences
- Evidence rejected because conclusions are morally undesirable
- 'It shouldn't be true, therefore it isn't' reasoning
- Moral discomfort treated as counter-evidence
- Research conclusions predetermined by values
- Facts denied because acknowledging them feels wrong
- Empirical questions answered by moral reasoning

When moral consideration of facts is appropriate:
- Moral implications noted alongside factual claims
- Values inform research priorities, not conclusions
- Ethical constraints on research methods (not findings)
- Moral context provided for factual claims
- Distinction between facts and their implications maintained
- Values motivate investigation, not predetermine results
- Moral reasoning applied to actions, not to facts

Output JSON with: fallacy_present (bool), severity (none/mild/moderate/severe), argument (what is argued), moral_belief (what moral belief drives the claim), factual_claim (what factual claim is derived), evidence_status (what evidence actually shows), recommendation (appropriate_moral_consideration/mild_ought_to_is/significant_moralistic_fallacy/major_values_as_evidence/separate_ought_from_is)."""

MORALISTIC_FALLACY_PROMPT = """Detect moralistic fallacy:

Argument: {argument}
Moral belief: {belief}
Factual claim: {factual}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is a factual claim being derived from moral beliefs rather than evidence? Return ONLY valid JSON."""


class MoralisticFallacyService:
    """Detects moralistic fallacy — deriving is from ought."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        belief: str = "",
        factual: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moralistic fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORALISTIC_FALLACY_PROMPT.format(
                argument=argument,
                belief=belief or "Not specified",
                factual=factual or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORALISTIC_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "fallacy_present": data.get("fallacy_present", False),
            "severity": data.get("severity", ""),
            "moral_belief": data.get("moral_belief", ""),
            "factual_claim": data.get("factual_claim", ""),
            "evidence_status": data.get("evidence_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
