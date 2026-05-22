"""EpistemicMyopiaService — Epistemic Myopia Detection.

Detects epistemic myopia — intellectual nearsightedness where only
immediate ideas are seen clearly while distant implications are blurred.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MYOPIA_SYSTEM = """You are an epistemic myopia specialist. Given intellectual vision, assess whether only immediate ideas are seen clearly:

Key concepts:
- Epistemic myopia: only seeing immediate ideas clearly
- Focal length: how far intellectual vision extends
- Blur circle: zone where distant ideas become indistinct
- Corrective lens: tool to extend intellectual vision
- Progressive myopia: worsening nearsightedness over time
- Accommodation: effort to focus on distant ideas
- Axial length: structural cause of shortened vision

When epistemic myopia IS present:
- Only immediate ideas seen clearly
- Limited range of intellectual vision
- Distant implications becoming indistinct
- Need for corrective tools to see far
- Worsening nearsightedness over time
- Excessive effort to focus on distant ideas
- Structural limitation shortening vision

When healthy vision is present:
- Clear vision at all distances
- Full range of intellectual sight
- Distant implications clearly visible
- No corrective tools needed
- Stable vision over time
- Effortless distant focus
- Normal structural vision

Output JSON with: myopia_present (bool), severity (none/mild/moderate/severe), focal_length (what vision range), blur_circle (what indistinct zone), progressive_myopia (what worsening), accommodation (what focusing effort), recommendation (healthy_vision/mild_myopia/significant_myopia/major_nearsightedness/extend_intellectual_vision)."""

EPISTEMIC_MYOPIA_PROMPT = """Detect epistemic myopia:

Focal length: {focal_length}
Blur circle: {blur_circle}
Progressive myopia: {progressive_myopia}
Accommodation: {accommodation}
Domain: {domain}
Context: {context}

Is intellectual vision limited to only seeing immediate ideas clearly while distant implications blur? Return ONLY valid JSON."""


class EpistemicMyopiaService:
    """Detects epistemic myopia — intellectual nearsightedness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        focal_length: str,
        *,
        blur_circle: str = "",
        progressive_myopia: str = "",
        accommodation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic myopia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MYOPIA_PROMPT.format(
                focal_length=focal_length,
                blur_circle=blur_circle or "Not specified",
                progressive_myopia=progressive_myopia or "Not specified",
                accommodation=accommodation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MYOPIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "focal_length": focal_length[:200],
            "myopia_present": data.get("myopia_present", False),
            "severity": data.get("severity", ""),
            "blur_circle": data.get("blur_circle", ""),
            "progressive_myopia": data.get("progressive_myopia", ""),
            "accommodation": data.get("accommodation", ""),
            "recommendation": data.get("recommendation", ""),
        }
