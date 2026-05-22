"""EpistemicRigidityService — Epistemic Rigidity Detection.

Detects epistemic rigidity — inability to update beliefs in response
to new evidence, where beliefs remain fixed regardless of
what evidence accumulates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RIGIDITY_SYSTEM = """You are an epistemic rigidity specialist. Given a belief and accumulating evidence, assess whether beliefs are failing to update:

Key concepts:
- Epistemic rigidity: beliefs not updating with evidence
- Update failure: new evidence not changing beliefs
- Fixed beliefs: beliefs unchanged regardless of evidence
- Evidence immunity: beliefs immune to evidential challenge
- Revision resistance: resistance to any belief revision
- Stale beliefs: beliefs outdated by new evidence
- Updating failure: Bayesian updating not occurring

When epistemic rigidity IS present:
- Beliefs not updating in response to new evidence
- Evidence accumulating without belief change
- Beliefs fixed regardless of what is learned
- Resistance to any revision despite evidence
- Beliefs outdated by available evidence
- Bayesian updating not occurring
- Evidence having no effect on belief

When appropriate stability is present:
- Beliefs stable because evidence supports them
- Updating proportionate to evidence strength
- Beliefs revised when evidence warrants
- Stability reflecting genuine support
- Resistance based on evidence evaluation
- Beliefs current with available evidence
- Updating occurring at appropriate rate

Output JSON with: rigidity_present (bool), severity (none/mild/moderate/severe), belief (what belief is held), evidence (what new evidence exists), update_expected (what update would be appropriate), resistance (what resistance exists), recommendation (appropriate_stability/mild_update_lag/significant_epistemic_rigidity/major_evidence_immunity/update_beliefs_proportionate_to_evidence)."""

EPISTEMIC_RIGIDITY_PROMPT = """Detect epistemic rigidity:

Belief held: {belief}
New evidence: {evidence}
Update made: {update}
Resistance: {resistance}
Domain: {domain}
Context: {context}

Are beliefs failing to update in response to new evidence? Return ONLY valid JSON."""


class EpistemicRigidityService:
    """Detects epistemic rigidity — beliefs not updating with evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        evidence: str = "",
        update: str = "",
        resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic rigidity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RIGIDITY_PROMPT.format(
                belief=belief,
                evidence=evidence or "Not specified",
                update=update or "Not specified",
                resistance=resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RIGIDITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "rigidity_present": data.get("rigidity_present", False),
            "severity": data.get("severity", ""),
            "evidence": data.get("evidence", ""),
            "update_expected": data.get("update_expected", ""),
            "resistance": data.get("resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }
