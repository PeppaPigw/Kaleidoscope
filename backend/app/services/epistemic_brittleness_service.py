"""EpistemicBrittlenessService — Epistemic Brittleness Detection.

Detects epistemic brittleness — belief systems that shatter rather
than adapt when challenged, where lack of flexibility means
any challenge threatens total collapse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRITTLENESS_SYSTEM = """You are an epistemic brittleness specialist. Given a belief system under challenge, assess whether it is brittle rather than resilient:

Key concepts:
- Epistemic brittleness: beliefs shatter rather than adapt
- All-or-nothing epistemology: total belief or total rejection
- Fragile certainty: certainty that cannot survive any challenge
- Adaptation failure: inability to partially revise
- Binary epistemology: no middle ground between belief and disbelief
- Catastrophic revision: any revision becoming total revision
- Flexibility absence: no capacity for gradual updating

When epistemic brittleness IS present:
- Beliefs shatter rather than adapt to challenges
- All-or-nothing response to evidence
- Certainty that cannot survive partial challenge
- Inability to partially revise beliefs
- Any challenge threatening total collapse
- No middle ground between full belief and rejection
- Catastrophic rather than gradual revision

When appropriate firmness is present:
- Beliefs resilient but responsive to evidence
- Partial revision possible and practiced
- Certainty proportionate and adjustable
- Challenges integrated without collapse
- Gradual updating in response to evidence
- Middle positions available and occupied
- Revision proportionate to evidence strength

Output JSON with: brittleness_present (bool), severity (none/mild/moderate/severe), belief_system (what belief system), challenge (what challenge is faced), response (how system responds), flexibility (what flexibility exists), recommendation (resilient_beliefs/mild_rigidity/significant_epistemic_brittleness/major_shatter_risk/develop_adaptive_belief_structures)."""

EPISTEMIC_BRITTLENESS_PROMPT = """Detect epistemic brittleness:

Belief system: {belief_system}
Challenge faced: {challenge}
Response pattern: {response}
Revision capacity: {revision}
Domain: {domain}
Context: {context}

Does the belief system shatter rather than adapt when challenged? Return ONLY valid JSON."""


class EpistemicBrittlenessService:
    """Detects epistemic brittleness — beliefs that shatter rather than adapt."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_system: str,
        *,
        challenge: str = "",
        response: str = "",
        revision: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic brittleness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRITTLENESS_PROMPT.format(
                belief_system=belief_system,
                challenge=challenge or "Not specified",
                response=response or "Not specified",
                revision=revision or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRITTLENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_system": belief_system[:200],
            "brittleness_present": data.get("brittleness_present", False),
            "severity": data.get("severity", ""),
            "challenge": data.get("challenge", ""),
            "response": data.get("response", ""),
            "flexibility": data.get("flexibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
