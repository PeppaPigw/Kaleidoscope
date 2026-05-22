"""IdentityProtectiveCognitionService — Identity-Protective Cognition Detection.

Detects identity-protective cognition — distorting reasoning to protect
identity-relevant beliefs, where threats to identity-defining beliefs
trigger defensive cognitive processing rather than fair evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IDENTITY_PROTECTIVE_COGNITION_SYSTEM = """You are an identity-protective cognition specialist. Given reasoning about an identity-relevant topic, assess whether identity is distorting cognition:

Key concepts:
- Identity-protective cognition: reasoning distorted by identity threat
- Belief-identity fusion: beliefs fused with sense of self
- Defensive processing: evidence processed defensively
- Identity threat response: cognitive defense against identity threat
- Motivated skepticism: skeptical only of identity-threatening evidence
- Asymmetric evaluation: different standards for identity-relevant info
- Tribal epistemics: truth determined by group membership

When identity-protective cognition IS present:
- Reasoning distorted by identity threat
- Evidence evaluated differently based on identity relevance
- Defensive processing triggered by identity-threatening information
- Skepticism applied asymmetrically based on identity
- Beliefs protected because identity-defining
- Group membership determining what's accepted as true
- Cognitive effort directed at defending rather than evaluating

When identity-relevant reasoning is appropriate:
- Identity acknowledged but not driving evaluation
- Evidence evaluated by same standards regardless of identity relevance
- Identity-threatening evidence given fair hearing
- Beliefs updated even when identity-relevant
- Group membership not determining truth
- Defensive reactions noticed and managed
- Identity and evidence distinguished

Output JSON with: protective_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning is observed), identity_threat (what identity is threatened), distortion (how reasoning is distorted), asymmetry (what asymmetry in evaluation exists), recommendation (fair_evaluation/mild_defensive_processing/significant_identity_protection/major_tribal_epistemics/evaluate_evidence_independently)."""

IDENTITY_PROTECTIVE_COGNITION_PROMPT = """Detect identity-protective cognition:

Reasoning: {reasoning}
Identity at stake: {identity}
Evidence evaluated: {evidence}
Evaluation pattern: {pattern}
Domain: {domain}
Context: {context}

Is reasoning being distorted to protect identity-relevant beliefs? Return ONLY valid JSON."""


class IdentityProtectiveCognitionService:
    """Detects identity-protective cognition — reasoning distorted by identity threat."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        identity: str = "",
        evidence: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect identity-protective cognition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IDENTITY_PROTECTIVE_COGNITION_PROMPT.format(
                reasoning=reasoning,
                identity=identity or "Not specified",
                evidence=evidence or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IDENTITY_PROTECTIVE_COGNITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "protective_present": data.get("protective_present", False),
            "severity": data.get("severity", ""),
            "identity_threat": data.get("identity_threat", ""),
            "distortion": data.get("distortion", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
