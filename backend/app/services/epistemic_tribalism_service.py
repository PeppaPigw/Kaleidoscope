"""EpistemicTribalismService — Epistemic Tribalism Detection.

Detects epistemic tribalism — evaluating claims based on tribal
membership rather than evidence, where what counts as true is
determined by group identity rather than epistemic merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRIBALISM_SYSTEM = """You are an epistemic tribalism specialist. Given a knowledge evaluation, assess whether tribal identity is determining truth:

Key concepts:
- Epistemic tribalism: truth determined by group membership
- Identity-based epistemology: who says it matters more than what
- Tribal truth: claims true because our group believes them
- Epistemic loyalty: believing what the group believes
- Out-group dismissal: rejecting claims from other groups
- Belief as badge: beliefs as group membership signals
- Epistemic polarization: groups diverging on factual claims

When epistemic tribalism IS present:
- Claims evaluated by source group not evidence
- Truth determined by tribal membership
- Out-group claims dismissed regardless of evidence
- Beliefs function as group loyalty signals
- Epistemic standards applied asymmetrically by group
- Factual claims polarized along group lines
- Evidence from wrong group automatically suspect

When community knowledge is appropriate:
- Claims evaluated on evidence regardless of source
- Group knowledge based on shared investigation
- Out-group claims engaged with substantively
- Beliefs held for epistemic not social reasons
- Standards applied consistently across groups
- Factual claims converge with evidence
- Source considered but doesn't determine truth

Output JSON with: tribalism_present (bool), severity (none/mild/moderate/severe), evaluation (what is evaluated), tribal_factor (what tribal factor operates), evidence_ignored (what evidence is ignored), group_signal (what belief signals), recommendation (appropriate_community_knowledge/mild_source_preference/significant_epistemic_tribalism/major_tribal_truth/evaluate_on_evidence)."""

EPISTEMIC_TRIBALISM_PROMPT = """Detect epistemic tribalism:

Evaluation: {evaluation}
Group dynamics: {groups}
Evidence handling: {evidence}
Source treatment: {source}
Domain: {domain}
Context: {context}

Is tribal identity determining what counts as true rather than evidence? Return ONLY valid JSON."""


class EpistemicTribalismService:
    """Detects epistemic tribalism — truth determined by group membership."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        groups: str = "",
        evidence: str = "",
        source: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tribalism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRIBALISM_PROMPT.format(
                evaluation=evaluation,
                groups=groups or "Not specified",
                evidence=evidence or "Not specified",
                source=source or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRIBALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "tribalism_present": data.get("tribalism_present", False),
            "severity": data.get("severity", ""),
            "tribal_factor": data.get("tribal_factor", ""),
            "evidence_ignored": data.get("evidence_ignored", ""),
            "group_signal": data.get("group_signal", ""),
            "recommendation": data.get("recommendation", ""),
        }
