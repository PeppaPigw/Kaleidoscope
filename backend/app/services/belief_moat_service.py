"""BeliefMoatService — Belief Moat Detection.

Detects belief moats — defensive structures around beliefs that
prevent revision regardless of evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_MOAT_SYSTEM = """You are a belief moat specialist. Given a belief defense pattern, assess whether defensive structures prevent legitimate revision:

Key concepts:
- Belief moat: defensive structure preventing belief revision
- Epistemic fortification: fortifying beliefs against all challenge
- Revision resistance: resisting revision regardless of evidence
- Defensive rationalization: rationalizing to defend rather than understand
- Immunization strategy: immunizing beliefs against disconfirmation
- Challenge deflection: deflecting all challenges regardless of merit
- Epistemic castle: building impregnable defenses around beliefs

When belief moat IS present:
- Defensive structures preventing legitimate revision
- Beliefs fortified against all challenge regardless of merit
- Revision resisted regardless of evidence quality
- Rationalization serving defense not understanding
- Beliefs immunized against any possible disconfirmation
- Challenges deflected regardless of their validity
- Impregnable defenses making beliefs unfalsifiable

When appropriate confidence is present:
- Beliefs held with confidence proportionate to evidence
- Challenges considered on their merits
- Revision possible given sufficient evidence
- Reasoning serving understanding not defense
- Beliefs open to disconfirmation in principle
- Challenges engaged with honestly
- Confidence revisable given new evidence

Output JSON with: moat_present (bool), severity (none/mild/moderate/severe), belief (what belief is defended), defense_structure (what defenses exist), revision_resistance (how revision is prevented), evidence_immunity (how evidence is deflected), recommendation (appropriate_confidence/mild_defensiveness/significant_belief_moat/major_epistemic_fortification/allow_belief_revision)."""

BELIEF_MOAT_PROMPT = """Detect belief moat:

Belief defended: {belief}
Defense structure: {defense}
Revision resistance: {resistance}
Evidence handling: {evidence}
Domain: {domain}
Context: {context}

Are defensive structures preventing legitimate belief revision? Return ONLY valid JSON."""


class BeliefMoatService:
    """Detects belief moats — defensive structures preventing revision."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        defense: str = "",
        resistance: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief moat."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_MOAT_PROMPT.format(
                belief=belief,
                defense=defense or "Not specified",
                resistance=resistance or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_MOAT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "moat_present": data.get("moat_present", False),
            "severity": data.get("severity", ""),
            "defense_structure": data.get("defense_structure", ""),
            "revision_resistance": data.get("revision_resistance", ""),
            "evidence_immunity": data.get("evidence_immunity", ""),
            "recommendation": data.get("recommendation", ""),
        }
