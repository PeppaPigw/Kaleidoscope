"""FramingEffectService — Framing Effect & Presentation Bias Detection.

Detects when the way information is presented (framed) is influencing
conclusions beyond what the underlying facts warrant. Same data,
different frame, different decision — that's a framing effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FRAMING_SYSTEM = """You are a framing effect specialist. Given a claim or presentation of information, assess whether framing is influencing the conclusion:
- How is the information currently framed?
- What alternative frames exist for the same underlying facts?
- Would the conclusion change under a different frame?
- Is the frame chosen to persuade rather than inform?
- What's the most neutral frame?

Output JSON with: framing_effect_present (bool), current_frame (how information is presented), alternative_frames (list of: frame, how_conclusion_changes), most_neutral_frame (the least biased presentation), frame_chosen_to_persuade (bool), persuasion_direction (what conclusion the frame pushes toward), underlying_facts (the frame-independent information), gain_vs_loss_frame (is this gain-framed or loss-framed?), reference_point (what's being used as the baseline), reframed_conclusion (conclusion under the most neutral frame), framing_techniques_used (list of: technique, effect), vulnerability (why this framing is effective on the audience), recommendation (frame_valid/reframe_needed/multiple_frames_needed)."""

FRAMING_PROMPT = """Detect framing effects:

Statement: {statement}
Context: {context}
Audience: {audience}
Domain: {domain}

Is framing influencing the conclusion? Return ONLY valid JSON."""


class FramingEffectService:
    """Detects framing effects in information presentation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        context: str = "",
        audience: str = "",
        domain: str = "",
    ) -> dict:
        """Detect framing effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FRAMING_PROMPT.format(
                statement=statement,
                context=context or "No additional context",
                audience=audience or "General audience",
                domain=domain or "general",
            ),
            system=FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "framing_effect_present": data.get("framing_effect_present", False),
            "current_frame": data.get("current_frame", ""),
            "alternative_frames": data.get("alternative_frames", []),
            "most_neutral_frame": data.get("most_neutral_frame", ""),
            "frame_chosen_to_persuade": data.get("frame_chosen_to_persuade", False),
            "persuasion_direction": data.get("persuasion_direction", ""),
            "underlying_facts": data.get("underlying_facts", ""),
            "gain_vs_loss_frame": data.get("gain_vs_loss_frame", ""),
            "reference_point": data.get("reference_point", ""),
            "reframed_conclusion": data.get("reframed_conclusion", ""),
            "framing_techniques_used": data.get("framing_techniques_used", []),
            "vulnerability": data.get("vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
