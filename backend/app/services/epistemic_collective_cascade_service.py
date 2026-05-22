"""EpistemicCollectiveCascadeService — Epistemic Collective Cascade Detection.

Detects epistemic collective cascade — information cascades where people
follow others rather than their own private signals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_CASCADE_SYSTEM = """You are an epistemic collective cascade specialist. Given sequential group behavior, assess whether an information cascade is causing people to follow others rather than private signals:

Key concepts:
- Epistemic cascade: sequential imitation overriding private information
- Sequential imitation: later actors copy earlier actors
- Private signal abandonment: personal evidence ignored
- Herding behavior: choices cluster because others chose first
- Cascade fragility: consensus can collapse when early signals are challenged
- Path dependence: early actions shape later beliefs
- Social proof substitution: others' behavior replaces evidence

When epistemic cascade IS present:
- Later actors imitate earlier choices
- Private evidence abandoned
- Herding replaces independent assessment
- Consensus depends heavily on early signals
- Social proof treated as evidence
- Contradictory signals withheld or discounted
- Group belief is fragile to new disclosures

When no cascade:
- Actors use private evidence independently
- Earlier choices inform but do not dominate
- Herding pressure resisted
- Consensus robust to sequence changes
- Evidence distinguished from social proof
- Contradictory signals considered
- Beliefs updated from substance

Output JSON with: cascade_detected (bool), severity (none/mild/moderate/severe), private_signal_abandonment (what private signals are ignored), herding_behavior (what imitation pattern appears), cascade_fragility (what could break the cascade), recommendation (no_cascade/mild_independent_signal_check/significant_private_evidence_review/major_sequence_reset/emergency_break_information_cascade)."""

EPISTEMIC_COLLECTIVE_CASCADE_PROMPT = """Detect epistemic collective cascade:

Sequential imitation: {sequential_imitation}
Private signal abandonment: {private_signal_abandonment}
Herding behavior: {herding_behavior}
Cascade fragility: {cascade_fragility}
Domain: {domain}
Context: {context}

Are people following others rather than their own private signals? Return ONLY valid JSON."""


class EpistemicCollectiveCascadeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        sequential_imitation: str,
        *,
        private_signal_abandonment: str = "",
        herding_behavior: str = "",
        cascade_fragility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_CASCADE_PROMPT.format(
                sequential_imitation=sequential_imitation,
                private_signal_abandonment=private_signal_abandonment or "Not specified",
                herding_behavior=herding_behavior or "Not specified",
                cascade_fragility=cascade_fragility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "sequential_imitation": sequential_imitation[:200],
            "cascade_detected": data.get("cascade_detected", False),
            "severity": data.get("severity", ""),
            "private_signal_abandonment": data.get("private_signal_abandonment", ""),
            "herding_behavior": data.get("herding_behavior", ""),
            "cascade_fragility": data.get("cascade_fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
