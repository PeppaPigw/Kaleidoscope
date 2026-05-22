"""ArgumentFromIncredulityService — Argument from Incredulity Detection.

Detects argument from incredulity — concluding that something is
false because one personally cannot imagine how it could be true.
The failure of imagination is treated as evidence against the claim.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARGUMENT_INCREDULITY_SYSTEM = """You are an argument from incredulity specialist. Given an argument, assess whether it concludes something is false because the arguer can't imagine how it could be true:

Key concepts:
- Argument from incredulity: "I can't see how X, therefore not X"
- Personal incredulity: treating inability to imagine as evidence
- Complexity argument: "this is too complex to have happened naturally"
- Failure of imagination: limited imagination ≠ limited reality
- Burden shifting: making the other side explain your confusion
- God of the gaps: inserting explanation where understanding fails
- Dunning-Kruger connection: not knowing enough to imagine the mechanism

When argument from incredulity IS present:
- "I can't imagine how X could work, therefore X is false"
- Personal inability to understand is treated as disproof
- "It's too complex/unlikely/strange to be true"
- The argument relies on the arguer's limited knowledge
- No positive evidence against the claim, just personal disbelief
- "How could X possibly..." as if the question is its own answer
- The arguer assumes their imagination bounds reality

When skepticism IS warranted:
- There are positive reasons to doubt the claim
- The incredulity is based on known physical constraints
- Expert knowledge informs the skepticism
- The claim violates well-established principles
- The skepticism is about evidence quality, not personal imagination
- Alternative explanations are more parsimonious
- The doubt is proportional to the claim's extraordinariness

Output JSON with: argument_from_incredulity_present (bool), severity (none/mild/moderate/severe), claim_doubted (what claim is doubted), basis (what the incredulity is based on), knowledge_gap (what knowledge would resolve the incredulity), positive_evidence (is there positive evidence against the claim), imagination_vs_reality (is imagination being confused with reality), recommendation (skepticism_warranted/mild_incredulity/significant_argument_from_incredulity/major_imagination_as_evidence/seek_positive_evidence)."""

ARGUMENT_INCREDULITY_PROMPT = """Detect argument from incredulity:

Argument: {argument}
Claim doubted: {claim}
Basis for doubt: {basis}
Evidence against: {evidence_against}
Domain: {domain}
Context: {context}

Is this argument concluding something is false because the arguer can't imagine how it could be true? Return ONLY valid JSON."""


class ArgumentFromIncredulityService:
    """Detects argument from incredulity — personal disbelief as evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        claim: str = "",
        basis: str = "",
        evidence_against: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect argument from incredulity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARGUMENT_INCREDULITY_PROMPT.format(
                argument=argument,
                claim=claim or "Not specified",
                basis=basis or "Not specified",
                evidence_against=evidence_against or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ARGUMENT_INCREDULITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "argument_from_incredulity_present": data.get("argument_from_incredulity_present", False),
            "severity": data.get("severity", ""),
            "claim_doubted": data.get("claim_doubted", ""),
            "knowledge_gap": data.get("knowledge_gap", ""),
            "positive_evidence": data.get("positive_evidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
