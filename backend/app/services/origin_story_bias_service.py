"""OriginStoryBiasService — Origin Story Bias Detection.

Detects origin story bias — constructing flattering or simplified
origin narratives that distort actual history, creating mythologized
accounts of how things began.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ORIGIN_STORY_BIAS_SYSTEM = """You are an origin story bias specialist. Given a founding or origin narrative, assess whether it distorts actual history:

Key concepts:
- Origin myth: simplified, flattering account of beginnings
- Founder mythology: attributing success to visionary individuals
- Garage myth: romanticizing humble beginnings
- Retroactive coherence: making early chaos seem planned
- Selective memory: remembering what supports the narrative
- Hero's journey imposition: forcing origin into mythic structure
- Sanitized history: removing uncomfortable truths from origin

When origin story bias IS present:
- Origin narrative significantly simplified from reality
- Uncomfortable facts omitted or minimized
- Individual genius emphasized over luck and context
- Early chaos presented as visionary planning
- Failures and pivots erased from narrative
- Origin story serves current political purposes
- Mythic structure imposed on messy reality

When origin accounts are balanced:
- Complexity of actual history preserved
- Luck and timing acknowledged alongside skill
- Failures and pivots included in narrative
- Multiple perspectives on origins represented
- Uncomfortable truths not sanitized
- Context and constraints acknowledged
- Origin story updated as new information emerges

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), narrative (what origin story), distortions (what is simplified or omitted), mythic_elements (what mythic structures are imposed), actual_history (what the more complex reality likely was), recommendation (balanced_account/mild_simplification/significant_mythologizing/major_origin_distortion/recover_actual_history)."""

ORIGIN_STORY_BIAS_PROMPT = """Detect origin story bias:

Narrative: {narrative}
Claims: {claims}
Known history: {history}
Purpose of narrative: {purpose}
Domain: {domain}
Context: {context}

Is this origin narrative distorting actual history? Return ONLY valid JSON."""


class OriginStoryBiasService:
    """Detects origin story bias — mythologized founding narratives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        claims: str = "",
        history: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect origin story bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ORIGIN_STORY_BIAS_PROMPT.format(
                narrative=narrative,
                claims=claims or "Not specified",
                history=history or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ORIGIN_STORY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "distortions": data.get("distortions", ""),
            "mythic_elements": data.get("mythic_elements", ""),
            "actual_history": data.get("actual_history", ""),
            "recommendation": data.get("recommendation", ""),
        }
