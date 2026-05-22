"""EpistemicFossilizationService — Epistemic Fossilization Detection.

Detects epistemic fossilization — the hardening of provisional
knowledge into dogma over time, where tentative conclusions become
unquestionable truths through repetition and institutional inertia.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FOSSILIZATION_SYSTEM = """You are an epistemic fossilization specialist. Given a knowledge claim, assess whether provisional knowledge has hardened into dogma:

Key concepts:
- Epistemic fossilization: provisional becoming dogmatic
- Textbook certainty: tentative findings presented as settled
- Citation ossification: old findings cited without re-evaluation
- Institutional inertia: organizations resisting knowledge update
- Paradigm rigidity: frameworks becoming unquestionable
- Replication assumption: assuming old findings still hold
- Knowledge calcification: flexibility lost over time

When epistemic fossilization IS present:
- Provisional findings treated as settled truth
- Tentative conclusions hardened through repetition
- Old findings cited without re-evaluation
- Institutional inertia prevents knowledge update
- Frameworks become unquestionable dogma
- Original caveats and limitations forgotten
- Knowledge no longer open to revision

When established knowledge is appropriate:
- Findings genuinely well-established
- Conclusions supported by extensive replication
- Knowledge updated when new evidence arrives
- Caveats and limitations preserved
- Frameworks open to challenge
- Institutional knowledge regularly reviewed
- Certainty proportional to evidence

Output JSON with: fossilization_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is fossilized), original_status (what original epistemic status was), current_status (what current status is), mechanism (how fossilization occurred), recommendation (appropriately_established/mild_certainty_creep/significant_epistemic_fossilization/major_knowledge_dogma/restore_provisionality)."""

EPISTEMIC_FOSSILIZATION_PROMPT = """Detect epistemic fossilization:

Knowledge claim: {claim}
Original status: {original}
Current treatment: {current}
Evidence updates: {updates}
Domain: {domain}
Context: {context}

Has provisional knowledge hardened into unquestionable dogma through time and repetition? Return ONLY valid JSON."""


class EpistemicFossilizationService:
    """Detects epistemic fossilization — provisional knowledge becoming dogma."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        original: str = "",
        current: str = "",
        updates: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fossilization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FOSSILIZATION_PROMPT.format(
                claim=claim,
                original=original or "Not specified",
                current=current or "Not specified",
                updates=updates or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FOSSILIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "fossilization_present": data.get("fossilization_present", False),
            "severity": data.get("severity", ""),
            "original_status": data.get("original_status", ""),
            "current_status": data.get("current_status", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
