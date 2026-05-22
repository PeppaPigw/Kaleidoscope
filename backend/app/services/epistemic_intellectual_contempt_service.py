"""EpistemicIntellectualContemptService — Epistemic Intellectual Contempt Detection.

Detects epistemic intellectual contempt — contempt for others'
intellectual capacities or contributions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_CONTEMPT_SYSTEM = """You are an epistemic intellectual contempt specialist. Given contempt for others' intellect, assess intellectual contempt:

Key concepts:
- Epistemic intellectual contempt: contempt for others' capacities
- Cognitive dismissal: treating others as intellectually beneath
- Capacity denial: refusing to acknowledge others' abilities
- Intellectual dehumanization: treating others as cognitively lesser
- Contemptuous framing: presenting others' ideas mockingly
- Superiority certainty: absolute conviction of intellectual superiority
- Worthlessness attribution: seeing others' contributions as worthless

When epistemic intellectual contempt IS present:
- Contempt for others' capacities
- Treating others as beneath
- Refusing to acknowledge abilities
- Treating as cognitively lesser
- Presenting ideas mockingly
- Absolute superiority conviction
- Seeing contributions as worthless

When no intellectual contempt:
- Respecting others' capacities
- Treating as intellectual equals
- Acknowledging abilities
- Recognizing cognitive diversity
- Presenting ideas fairly
- Humble about own abilities
- Valuing contributions

Output JSON with: intellectual_contempt_detected (bool), severity (none/mild/moderate/severe), cognitive_dismissal (what treating as beneath), capacity_denial (what refusing to acknowledge), contemptuous_framing (what presenting mockingly), superiority_certainty (what convinced superior about), recommendation (no_intellectual_contempt/mild_humility_practice/significant_respect_building/major_intensive_contempt_processing/emergency_active_dehumanization)."""

EPISTEMIC_INTELLECTUAL_CONTEMPT_PROMPT = """Detect epistemic intellectual contempt:

Cognitive dismissal: {cognitive_dismissal}
Capacity denial: {capacity_denial}
Contemptuous framing: {contemptuous_framing}
Superiority certainty: {superiority_certainty}
Domain: {domain}
Context: {context}

Is there contempt for others' intellectual capacities? Return ONLY valid JSON."""


class EpistemicIntellectualContemptService:
    """Detects epistemic intellectual contempt — contempt for others' capacities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cognitive_dismissal: str,
        *,
        capacity_denial: str = "",
        contemptuous_framing: str = "",
        superiority_certainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual contempt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_CONTEMPT_PROMPT.format(
                cognitive_dismissal=cognitive_dismissal,
                capacity_denial=capacity_denial or "Not specified",
                contemptuous_framing=contemptuous_framing or "Not specified",
                superiority_certainty=superiority_certainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_CONTEMPT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cognitive_dismissal": cognitive_dismissal[:200],
            "intellectual_contempt_detected": data.get("intellectual_contempt_detected", False),
            "severity": data.get("severity", ""),
            "capacity_denial": data.get("capacity_denial", ""),
            "contemptuous_framing": data.get("contemptuous_framing", ""),
            "superiority_certainty": data.get("superiority_certainty", ""),
            "recommendation": data.get("recommendation", ""),
        }
