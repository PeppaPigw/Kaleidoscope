"""EpistemicIntellectualRivalryService — Epistemic Intellectual Rivalry Detection.

Detects epistemic intellectual rivalry — rivalry that distorts intellectual
positions to oppose or outdo another thinker.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_RIVALRY_SYSTEM = """You are an epistemic intellectual rivalry specialist. Given rivalry distorting positions, assess intellectual rivalry:

Key concepts:
- Epistemic intellectual rivalry: rivalry distorting intellectual positions
- Oppositional positioning: taking positions primarily to oppose rival
- Competitive distortion: distorting views to outdo competitor
- Status-driven thinking: thinking shaped by status competition
- Intellectual one-upmanship: always needing to be more clever
- Rivalry blindness: blind spots created by rivalry dynamics
- Position as weapon: using intellectual positions as weapons against rival

When epistemic intellectual rivalry IS present:
- Rivalry distorting positions
- Taking positions to oppose rival
- Distorting views to outdo competitor
- Thinking shaped by status competition
- Always needing to be more clever
- Blind spots from rivalry
- Using positions as weapons

When no intellectual rivalry:
- Positions independent of rivals
- Genuine intellectual engagement
- Views undistorted by competition
- Thinking independent of status
- Comfortable with others being clever
- No rivalry blind spots
- Positions as genuine beliefs

Output JSON with: intellectual_rivalry_detected (bool), severity (none/mild/moderate/severe), oppositional_positioning (what opposing to counter rival), competitive_distortion (what distorting to outdo), status_driven_thinking (what shaped by status), rivalry_blindness (what blind to because of rivalry), recommendation (no_intellectual_rivalry/mild_independence_check/significant_rivalry_awareness/major_intensive_disentanglement/emergency_complete_rivalry_distortion)."""

EPISTEMIC_INTELLECTUAL_RIVALRY_PROMPT = """Detect epistemic intellectual rivalry:

Oppositional positioning: {oppositional_positioning}
Competitive distortion: {competitive_distortion}
Status driven thinking: {status_driven_thinking}
Rivalry blindness: {rivalry_blindness}
Domain: {domain}
Context: {context}

Is there rivalry distorting intellectual positions? Return ONLY valid JSON."""


class EpistemicIntellectualRivalryService:
    """Detects epistemic intellectual rivalry — rivalry distorting positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        oppositional_positioning: str,
        *,
        competitive_distortion: str = "",
        status_driven_thinking: str = "",
        rivalry_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual rivalry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_RIVALRY_PROMPT.format(
                oppositional_positioning=oppositional_positioning,
                competitive_distortion=competitive_distortion or "Not specified",
                status_driven_thinking=status_driven_thinking or "Not specified",
                rivalry_blindness=rivalry_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_RIVALRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "oppositional_positioning": oppositional_positioning[:200],
            "intellectual_rivalry_detected": data.get("intellectual_rivalry_detected", False),
            "severity": data.get("severity", ""),
            "competitive_distortion": data.get("competitive_distortion", ""),
            "status_driven_thinking": data.get("status_driven_thinking", ""),
            "rivalry_blindness": data.get("rivalry_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
