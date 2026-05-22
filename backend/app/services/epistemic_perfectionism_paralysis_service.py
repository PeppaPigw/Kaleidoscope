"""EpistemicPerfectionismParalysisService — Epistemic Perfectionism Paralysis Detection.

Detects epistemic perfectionism paralysis — inability to act or conclude
due to impossibly high intellectual standards.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERFECTIONISM_PARALYSIS_SYSTEM = """You are an epistemic perfectionism paralysis specialist. Given paralysis from impossible standards, assess perfectionism:

Key concepts:
- Epistemic perfectionism paralysis: frozen by impossible standards
- All-or-nothing: if not perfect, worthless
- Procrastination: avoiding starting due to perfection demand
- Completion failure: never finishing because never good enough
- Self-criticism: harsh judgment of own intellectual output
- Standard inflation: standards always rising beyond reach
- Output suppression: not sharing because not perfect

When epistemic perfectionism paralysis IS present:
- Frozen by impossible standards
- If not perfect, worthless
- Avoiding starting
- Never finishing
- Harsh self-judgment
- Standards always rising
- Not sharing output

When no perfectionism paralysis:
- Comfortable with good enough
- Valuing imperfect work
- Starting readily
- Completing work
- Self-compassionate assessment
- Stable realistic standards
- Sharing freely

Output JSON with: perfectionism_paralysis_detected (bool), severity (none/mild/moderate/severe), impossible_standards (what demanding), completion_failure (what not finishing), self_criticism (what judging), output_suppression (what not sharing), recommendation (no_perfectionism_paralysis/mild_standard_relaxation/significant_good_enough_practice/major_intensive_perfectionism_therapy/emergency_complete_paralysis)."""

EPISTEMIC_PERFECTIONISM_PARALYSIS_PROMPT = """Detect epistemic perfectionism paralysis:

Impossible standards: {impossible_standards}
Completion failure: {completion_failure}
Self criticism: {self_criticism}
Output suppression: {output_suppression}
Domain: {domain}
Context: {context}

Is there paralysis from impossibly high intellectual standards? Return ONLY valid JSON."""


class EpistemicPerfectionismParalysisService:
    """Detects epistemic perfectionism paralysis — frozen by impossible standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        impossible_standards: str,
        *,
        completion_failure: str = "",
        self_criticism: str = "",
        output_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic perfectionism paralysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERFECTIONISM_PARALYSIS_PROMPT.format(
                impossible_standards=impossible_standards,
                completion_failure=completion_failure or "Not specified",
                self_criticism=self_criticism or "Not specified",
                output_suppression=output_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERFECTIONISM_PARALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "impossible_standards": impossible_standards[:200],
            "perfectionism_paralysis_detected": data.get("perfectionism_paralysis_detected", False),
            "severity": data.get("severity", ""),
            "completion_failure": data.get("completion_failure", ""),
            "self_criticism": data.get("self_criticism", ""),
            "output_suppression": data.get("output_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
