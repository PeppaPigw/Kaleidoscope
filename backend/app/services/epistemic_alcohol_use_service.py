"""EpistemicAlcoholUseService — Epistemic Alcohol Use Detection.

Detects epistemic alcohol use — using intellectual numbing agents to
escape cognitive discomfort and avoid difficult thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ALCOHOL_SYSTEM = """You are an epistemic alcohol use specialist. Given intellectual numbing, assess alcohol use patterns:

Key concepts:
- Epistemic alcohol use: using numbing to escape cognitive discomfort
- Self-medication: numbing to avoid difficult thoughts
- Disinhibition: lowered intellectual standards while numbed
- Blackout: complete loss of intellectual memory
- Tolerance: needing more numbing for same relief
- Social drinking: numbing in group intellectual settings
- Functional impairment: numbing affecting intellectual performance

When epistemic alcohol use IS present:
- Using numbing to escape discomfort
- Self-medicating difficult thoughts
- Lowered standards while numbed
- Loss of intellectual memory
- Needing more numbing
- Numbing in group settings
- Affecting performance

When no alcohol use:
- Facing discomfort directly
- Processing difficult thoughts
- Consistent standards
- Complete memory
- No numbing needed
- Clear in group settings
- Unimpaired performance

Output JSON with: alcohol_use_detected (bool), severity (none/mild/moderate/severe), numbing_pattern (what escape behavior), self_medication (what avoidance), impairment_level (what performance loss), tolerance_progression (what escalation), recommendation (no_alcohol_use/mild_harm_reduction/significant_structured_reduction/major_intensive_treatment/emergency_severe_impairment)."""

EPISTEMIC_ALCOHOL_PROMPT = """Detect epistemic alcohol use:

Numbing pattern: {numbing_pattern}
Self medication: {self_medication}
Impairment level: {impairment_level}
Tolerance progression: {tolerance_progression}
Domain: {domain}
Context: {context}

Is there intellectual numbing to escape cognitive discomfort? Return ONLY valid JSON."""


class EpistemicAlcoholUseService:
    """Detects epistemic alcohol use — intellectual numbing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        numbing_pattern: str,
        *,
        self_medication: str = "",
        impairment_level: str = "",
        tolerance_progression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic alcohol use."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ALCOHOL_PROMPT.format(
                numbing_pattern=numbing_pattern,
                self_medication=self_medication or "Not specified",
                impairment_level=impairment_level or "Not specified",
                tolerance_progression=tolerance_progression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ALCOHOL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "numbing_pattern": numbing_pattern[:200],
            "alcohol_use_detected": data.get("alcohol_use_detected", False),
            "severity": data.get("severity", ""),
            "self_medication": data.get("self_medication", ""),
            "impairment_level": data.get("impairment_level", ""),
            "tolerance_progression": data.get("tolerance_progression", ""),
            "recommendation": data.get("recommendation", ""),
        }
