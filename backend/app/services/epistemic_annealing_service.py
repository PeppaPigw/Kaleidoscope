"""EpistemicAnnealingService — Epistemic Annealing Failure Detection.

Detects epistemic annealing failure — internal stresses in knowledge
not properly relieved, leading to unexpected failures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANNEALING_SYSTEM = """You are an epistemic annealing specialist. Given a knowledge structure, assess whether internal stresses remain unrelieved:

Key concepts:
- Epistemic annealing: relieving internal stresses in knowledge through careful review
- Internal stress: hidden tensions within knowledge structure
- Stress accumulation: stresses building up without relief
- Unexpected failure: failure from accumulated internal stress
- Relief process: careful review that relieves tensions
- Hidden tension: tensions not visible on surface
- Stress concentration: points where stress concentrates

When annealing failure IS present:
- Internal stresses in knowledge not relieved
- Hidden tensions within knowledge structure
- Stresses building up without review
- Risk of unexpected failure from accumulated stress
- No careful review process to relieve tensions
- Tensions not visible on surface but present
- Stress concentrated at specific points

When properly annealed knowledge is present:
- Internal stresses properly relieved
- No hidden tensions in knowledge structure
- Stresses addressed through careful review
- Low risk of unexpected failure
- Regular review process relieving tensions
- Tensions visible and addressed
- No dangerous stress concentrations

Output JSON with: annealing_failure (bool), severity (none/mild/moderate/severe), knowledge (what knowledge has stress), stress (what internal stresses exist), accumulation (how stress accumulates), concentration (where stress concentrates), recommendation (properly_annealed/mild_stress/significant_annealing_failure/major_stress_accumulation/relieve_internal_stress)."""

EPISTEMIC_ANNEALING_PROMPT = """Detect epistemic annealing failure:

Knowledge: {knowledge}
Stress: {stress}
Accumulation: {accumulation}
Concentration: {concentration}
Domain: {domain}
Context: {context}

Does knowledge have unrelieved internal stresses that risk unexpected failure? Return ONLY valid JSON."""


class EpistemicAnnealingService:
    """Detects epistemic annealing failure — unrelieved internal stresses in knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        stress: str = "",
        accumulation: str = "",
        concentration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic annealing failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANNEALING_PROMPT.format(
                knowledge=knowledge,
                stress=stress or "Not specified",
                accumulation=accumulation or "Not specified",
                concentration=concentration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANNEALING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "annealing_failure": data.get("annealing_failure", False),
            "severity": data.get("severity", ""),
            "stress": data.get("stress", ""),
            "accumulation": data.get("accumulation", ""),
            "concentration": data.get("concentration", ""),
            "recommendation": data.get("recommendation", ""),
        }
