"""EpistemicExistentialGuiltService — Epistemic Existential Guilt Detection.

Detects epistemic existential guilt — guilt from failing to fulfill one's
intellectual potential or betraying one's authentic epistemic self.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXISTENTIAL_GUILT_SYSTEM = """You are an epistemic existential guilt specialist. Given intellectual potential failure, assess existential guilt:

Key concepts:
- Epistemic existential guilt: guilt from unfulfilled potential
- Authenticity failure: not being true to intellectual self
- Wasted potential: could have contributed more
- Inauthenticity: living someone else's intellectual life
- Responsibility avoidance: not taking intellectual ownership
- Self-betrayal: knowing better but not doing better
- Unlived intellectual life: the path not taken

When epistemic existential guilt IS present:
- Guilt from unfulfilled potential
- Not true to intellectual self
- Could have contributed more
- Living others' intellectual life
- Not taking ownership
- Knowing better but not doing
- Path not taken haunting

When no existential guilt:
- Fulfilled potential
- Authentic intellectual self
- Contributing fully
- Living own intellectual life
- Taking ownership
- Acting on knowledge
- At peace with choices

Output JSON with: existential_guilt_detected (bool), severity (none/mild/moderate/severe), authenticity_failure (what not true), wasted_potential (what could have), self_betrayal (what knowing better), unlived_life (what path not taken), recommendation (no_existential_guilt/mild_authenticity_work/significant_existential_therapy/major_intensive_reconstruction/emergency_complete_paralysis)."""

EPISTEMIC_EXISTENTIAL_GUILT_PROMPT = """Detect epistemic existential guilt:

Authenticity failure: {authenticity_failure}
Wasted potential: {wasted_potential}
Self betrayal: {self_betrayal}
Unlived life: {unlived_life}
Domain: {domain}
Context: {context}

Is there guilt from failing to fulfill intellectual potential or betraying authentic self? Return ONLY valid JSON."""


class EpistemicExistentialGuiltService:
    """Detects epistemic existential guilt — guilt from unfulfilled potential."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        authenticity_failure: str,
        *,
        wasted_potential: str = "",
        self_betrayal: str = "",
        unlived_life: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic existential guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXISTENTIAL_GUILT_PROMPT.format(
                authenticity_failure=authenticity_failure,
                wasted_potential=wasted_potential or "Not specified",
                self_betrayal=self_betrayal or "Not specified",
                unlived_life=unlived_life or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXISTENTIAL_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authenticity_failure": authenticity_failure[:200],
            "existential_guilt_detected": data.get("existential_guilt_detected", False),
            "severity": data.get("severity", ""),
            "wasted_potential": data.get("wasted_potential", ""),
            "self_betrayal": data.get("self_betrayal", ""),
            "unlived_life": data.get("unlived_life", ""),
            "recommendation": data.get("recommendation", ""),
        }
