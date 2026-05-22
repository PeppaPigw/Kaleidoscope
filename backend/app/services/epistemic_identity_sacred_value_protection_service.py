"""EpistemicIdentitySacredValueProtectionService — Epistemic Identity Sacred Value Protection Detection.

Detects sacred value protection where protected moral commitments distort
evidence evaluation and belief updating.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_SACRED_VALUE_PROTECTION_SYSTEM = """You are an epistemic identity sacred value protection specialist. Given protected-value patterns, assess evidence distortion around sacred commitments:

Key concepts:
- Sacred value protection: protected values distort evidence evaluation
- Taboo tradeoff avoidance: factual tradeoffs are rejected as morally impermissible
- Moral outrage as evidence: outrage is treated as proof
- Protected belief immunity: beliefs tied to sacred values are shielded from testing
- Heresy framing: disagreement is treated as moral betrayal rather than evidence

When sacred value protection IS present:
- Taboo tradeoffs block evaluation
- Moral outrage substitutes for evidence
- Protected beliefs become immune
- Dissent is framed as heresy
- Accuracy is subordinated to sacred commitments

When no sacred value protection:
- Values and evidence are distinguished
- Tradeoffs can be described without endorsement
- Outrage is not treated as proof
- Protected beliefs remain testable
- Disagreement can be evaluated on evidence

Output JSON with: sacred_value_protection_detected (bool), severity (none/mild/moderate/severe), moral_outrage_as_evidence (where outrage substitutes for proof), protected_belief_immunity (what belief is shielded), heresy_framing (what disagreement is moralized), recommendation (no_sacred_value_protection/mild_value_evidence_separation/significant_tradeoff_review/major_belief_testing/emergency_complete_sacred_value_decoupling)."""

EPISTEMIC_IDENTITY_SACRED_VALUE_PROTECTION_PROMPT = """Detect epistemic identity sacred value protection:

Taboo tradeoff avoidance: {taboo_tradeoff_avoidance}
Moral outrage as evidence: {moral_outrage_as_evidence}
Protected belief immunity: {protected_belief_immunity}
Heresy framing: {heresy_framing}
Domain: {domain}
Context: {context}

Are sacred values distorting evidence evaluation? Return ONLY valid JSON."""


class EpistemicIdentitySacredValueProtectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        taboo_tradeoff_avoidance: str,
        *,
        moral_outrage_as_evidence: str = "",
        protected_belief_immunity: str = "",
        heresy_framing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_SACRED_VALUE_PROTECTION_PROMPT.format(
                taboo_tradeoff_avoidance=taboo_tradeoff_avoidance,
                moral_outrage_as_evidence=moral_outrage_as_evidence or "Not specified",
                protected_belief_immunity=protected_belief_immunity or "Not specified",
                heresy_framing=heresy_framing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_SACRED_VALUE_PROTECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "taboo_tradeoff_avoidance": taboo_tradeoff_avoidance[:200],
            "sacred_value_protection_detected": data.get("sacred_value_protection_detected", False),
            "severity": data.get("severity", ""),
            "moral_outrage_as_evidence": data.get("moral_outrage_as_evidence", ""),
            "protected_belief_immunity": data.get("protected_belief_immunity", ""),
            "heresy_framing": data.get("heresy_framing", ""),
            "recommendation": data.get("recommendation", ""),
        }
