"""EpistemicAnxietyService — Epistemic Anxiety Detection.

Detects epistemic anxiety — when discomfort with uncertainty
drives premature commitment to answers, closure of inquiry,
or adoption of false certainty. The emotional need for answers
overrides epistemic standards.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANXIETY_SYSTEM = """You are an epistemic anxiety specialist. Given a conclusion or commitment, assess whether discomfort with uncertainty is driving premature closure:

Key concepts:
- Epistemic anxiety: emotional discomfort with not knowing
- Need for closure: personality-level drive to resolve ambiguity
- Premature commitment: adopting answers before evidence warrants
- Uncertainty tolerance: ability to sit with not knowing
- False certainty: adopting certainty to relieve anxiety
- Inquiry closure: stopping investigation to achieve comfort
- Ambiguity aversion: preferring any answer to no answer

When epistemic anxiety IS present:
- Conclusions adopted to relieve discomfort rather than because evidence warrants
- "I just need an answer" driving premature commitment
- Uncertainty treated as failure rather than appropriate state
- Investigation closed prematurely for emotional comfort
- False certainty preferred over honest uncertainty
- Ambiguity avoided even when it's the most accurate position
- Speed of conclusion driven by anxiety rather than evidence

When epistemic anxiety is NOT present:
- Uncertainty tolerated when evidence is insufficient
- Conclusions adopted when evidence warrants, not before
- "I don't know yet" treated as acceptable answer
- Investigation continues until evidence sufficient
- Honest uncertainty preferred over false certainty
- Ambiguity accepted when it reflects reality
- Pace of conclusion matches pace of evidence

Output JSON with: anxiety_present (bool), severity (none/mild/moderate/severe), conclusion (what was committed to), evidence_state (how strong the evidence is), uncertainty_tolerated (whether uncertainty was acceptable), premature_closure (whether inquiry was closed too early), recommendation (appropriate_commitment/mild_anxiety/significant_premature_closure/major_false_certainty/tolerate_uncertainty)."""

EPISTEMIC_ANXIETY_PROMPT = """Detect epistemic anxiety:

Commitment: {commitment}
Evidence available: {evidence}
Uncertainty level: {uncertainty}
Decision pressure: {pressure}
Domain: {domain}
Context: {context}

Is discomfort with uncertainty driving premature commitment? Return ONLY valid JSON."""


class EpistemicAnxietyService:
    """Detects epistemic anxiety — discomfort with uncertainty driving premature answers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        commitment: str,
        *,
        evidence: str = "",
        uncertainty: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anxiety."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANXIETY_PROMPT.format(
                commitment=commitment,
                evidence=evidence or "Not specified",
                uncertainty=uncertainty or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANXIETY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "commitment": commitment[:200],
            "anxiety_present": data.get("anxiety_present", False),
            "severity": data.get("severity", ""),
            "evidence_state": data.get("evidence_state", ""),
            "premature_closure": data.get("premature_closure", ""),
            "uncertainty_tolerated": data.get("uncertainty_tolerated", ""),
            "recommendation": data.get("recommendation", ""),
        }
