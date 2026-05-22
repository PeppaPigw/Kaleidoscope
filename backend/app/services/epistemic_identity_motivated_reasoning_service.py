"""EpistemicIdentityMotivatedReasoningService — Epistemic Identity Motivated Reasoning Detection.

Detects identity-protective motivated reasoning where evidence is processed
to defend identity-linked conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_MOTIVATED_REASONING_SYSTEM = """You are an epistemic identity motivated reasoning specialist. Given identity-threat patterns, assess identity-protective reasoning:

Key concepts:
- Identity-protective motivated reasoning: reasoning bends to defend identity-linked beliefs
- Identity threat response: evidence is treated as a threat to self or group identity
- Belief defense: arguments are selected to protect existing beliefs
- Evidence asymmetry: friendly evidence gets less scrutiny than hostile evidence
- Conclusion-first reasoning: reasoning works backward from a protected conclusion

When motivated reasoning IS present:
- Identity threat drives evaluation
- Beliefs are defended before tested
- Evidence receives asymmetric scrutiny
- Conclusions precede reasons
- Accuracy goals are subordinated to identity protection

When no motivated reasoning:
- Identity threat is separated from evidence
- Beliefs remain testable
- Evidence receives symmetric scrutiny
- Conclusions follow reasons
- Accuracy remains the governing goal

Output JSON with: motivated_reasoning_detected (bool), severity (none/mild/moderate/severe), belief_defense (what belief is being defended), evidence_asymmetry (what evidence receives asymmetric scrutiny), conclusion_first_reasoning (what conclusion precedes reasons), recommendation (no_motivated_reasoning/mild_identity_distancing/significant_symmetric_review/major_belief_audit/emergency_complete_identity_decoupling)."""

EPISTEMIC_IDENTITY_MOTIVATED_REASONING_PROMPT = """Detect epistemic identity motivated reasoning:

Identity threat response: {identity_threat_response}
Belief defense: {belief_defense}
Evidence asymmetry: {evidence_asymmetry}
Conclusion-first reasoning: {conclusion_first_reasoning}
Domain: {domain}
Context: {context}

Is identity protection distorting reasoning and evidence evaluation? Return ONLY valid JSON."""


class EpistemicIdentityMotivatedReasoningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        identity_threat_response: str,
        *,
        belief_defense: str = "",
        evidence_asymmetry: str = "",
        conclusion_first_reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_MOTIVATED_REASONING_PROMPT.format(
                identity_threat_response=identity_threat_response,
                belief_defense=belief_defense or "Not specified",
                evidence_asymmetry=evidence_asymmetry or "Not specified",
                conclusion_first_reasoning=conclusion_first_reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_MOTIVATED_REASONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "identity_threat_response": identity_threat_response[:200],
            "motivated_reasoning_detected": data.get("motivated_reasoning_detected", False),
            "severity": data.get("severity", ""),
            "belief_defense": data.get("belief_defense", ""),
            "evidence_asymmetry": data.get("evidence_asymmetry", ""),
            "conclusion_first_reasoning": data.get("conclusion_first_reasoning", ""),
            "recommendation": data.get("recommendation", ""),
        }
