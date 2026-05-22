"""EpistemicLensService — Epistemic Lens Detection.

Detects epistemic lens distortion — distorting lenses applied to
knowledge that systematically warp perception.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LENS_SYSTEM = """You are an epistemic lens specialist. Given a knowledge perception pattern, assess whether distorting lenses are applied:

Key concepts:
- Epistemic lens: framework that shapes how knowledge is perceived
- Distortion: systematic warping of knowledge through a lens
- Magnification: making some aspects appear larger than they are
- Minimization: making some aspects appear smaller than they are
- Chromatic aberration: different aspects distorted differently
- Focal bias: only seeing what's in focus, missing periphery
- Lens awareness: whether the lens itself is acknowledged

When epistemic lens distortion IS present:
- Distorting framework systematically warping knowledge
- Some aspects magnified beyond their actual importance
- Some aspects minimized below their actual importance
- Different aspects distorted in different ways
- Only seeing what the lens focuses on
- Missing peripheral knowledge outside lens focus
- Lens not acknowledged as a lens

When clear perception is present:
- No distorting framework warping knowledge
- Aspects perceived at their actual importance
- Nothing systematically minimized
- Consistent perception across aspects
- Full field of view maintained
- Peripheral knowledge included
- Any lenses acknowledged and accounted for

Output JSON with: lens_distortion (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is distorted), lens (what lens is applied), magnification (what is magnified), minimization (what is minimized), recommendation (clear_perception/mild_distortion/significant_lens_effect/major_warping/acknowledge_and_correct_lens)."""

EPISTEMIC_LENS_PROMPT = """Detect epistemic lens distortion:

Knowledge: {knowledge}
Lens: {lens}
Magnification: {magnification}
Minimization: {minimization}
Domain: {domain}
Context: {context}

Is a distorting lens systematically warping how knowledge is perceived? Return ONLY valid JSON."""


class EpistemicLensService:
    """Detects epistemic lens distortion — distorting frameworks warping knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        lens: str = "",
        magnification: str = "",
        minimization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lens distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LENS_PROMPT.format(
                knowledge=knowledge,
                lens=lens or "Not specified",
                magnification=magnification or "Not specified",
                minimization=minimization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LENS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "lens_distortion": data.get("lens_distortion", False),
            "severity": data.get("severity", ""),
            "lens": data.get("lens", ""),
            "magnification": data.get("magnification", ""),
            "minimization": data.get("minimization", ""),
            "recommendation": data.get("recommendation", ""),
        }
