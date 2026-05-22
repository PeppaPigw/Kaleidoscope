"""BeliefPerseveranceService — Belief Perseverance Detection.

Detects belief perseverance — maintaining beliefs even after the
evidence that originally supported them has been completely
discredited. Ross, Lepper & Hubbard (1975). Once a belief forms,
it becomes self-sustaining through biased memory, selective
attention, and causal explanations that survive the original data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_SYSTEM = """You are a belief perseverance specialist. Given a belief and its evidential status, assess whether belief perseverance is maintaining a discredited position:

Key concepts (Ross, Lepper & Hubbard, 1975):
- Belief perseverance: beliefs survive the discrediting of their evidential basis
- Debriefing failure: even explicit debriefing doesn't fully eliminate the belief
- Causal model persistence: once you've built a causal story, removing the data doesn't remove the story
- Biased assimilation: new evidence is interpreted to support existing beliefs
- Selective memory: remembering confirming evidence, forgetting disconfirming
- Explanation-based persistence: having explained WHY something is true makes it feel true

When belief perseverance IS present:
- Original evidence has been discredited but belief remains
- The person acknowledges the evidence is gone but still "feels" the belief is true
- New evidence is being filtered through the old belief
- Causal explanations generated for the belief persist independently
- "I know the study was retracted, but I still think..."

When maintaining a belief IS appropriate:
- Other independent evidence still supports it
- The discrediting was partial, not complete
- The belief was formed from multiple sources, only one was discredited
- There are strong theoretical reasons independent of the discredited evidence

Output JSON with: belief_perseverance_present (bool), severity (none/mild/moderate/severe), belief (what belief is being maintained), original_evidence (what originally supported it), discrediting_event (what undermined the evidence), current_evidential_status (what evidence remains), causal_model_persists (bool — does the explanatory story survive?), biased_assimilation (bool — is new evidence being filtered?), selective_memory (bool — remembering only confirming data?), independent_support (what other evidence exists), emotional_investment (how much identity is tied to the belief), social_reinforcement (bool — is the belief socially maintained?), update_resistance (what makes updating difficult), bayesian_ideal (what belief strength the evidence actually warrants), belief_vs_evidence_gap (how far the belief is from what evidence supports), recommendation (belief_supported/mild_perseverance/significant_perseverance/major_belief_evidence_gap/update_belief)."""

BELIEF_PROMPT = """Detect belief perseverance:

Belief held: {belief}
Original evidence: {original_evidence}
Discrediting information: {discrediting}
Current stance: {current_stance}
Domain: {domain}
Context: {context}

Is belief perseverance maintaining a discredited position? Return ONLY valid JSON."""


class BeliefPerseveranceService:
    """Detects belief perseverance — maintaining beliefs after evidence is discredited."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        original_evidence: str = "",
        discrediting: str = "",
        current_stance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief perseverance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_PROMPT.format(
                belief=belief,
                original_evidence=original_evidence or "Not specified",
                discrediting=discrediting or "Not specified",
                current_stance=current_stance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "belief_perseverance_present": data.get("belief_perseverance_present", False),
            "severity": data.get("severity", ""),
            "original_evidence": data.get("original_evidence", ""),
            "discrediting_event": data.get("discrediting_event", ""),
            "current_evidential_status": data.get("current_evidential_status", ""),
            "causal_model_persists": data.get("causal_model_persists", False),
            "biased_assimilation": data.get("biased_assimilation", False),
            "selective_memory": data.get("selective_memory", False),
            "independent_support": data.get("independent_support", ""),
            "emotional_investment": data.get("emotional_investment", ""),
            "social_reinforcement": data.get("social_reinforcement", False),
            "update_resistance": data.get("update_resistance", ""),
            "bayesian_ideal": data.get("bayesian_ideal", ""),
            "belief_vs_evidence_gap": data.get("belief_vs_evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
