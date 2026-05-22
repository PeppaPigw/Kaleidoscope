"""EpistemicCrevassService — Epistemic Crevasse Detection.

Detects epistemic crevasses — hidden gaps in knowledge that are
covered by thin bridges of assumption, causing sudden falls.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CREVASSE_SYSTEM = """You are an epistemic crevasse specialist. Given a knowledge gap pattern, assess whether hidden gaps covered by thin assumptions cause sudden falls:

Key concepts:
- Epistemic crevasse: hidden gap covered by thin assumption bridge
- Snow bridge: thin layer of assumption covering deep gap
- Sudden fall: unexpected plunge into knowledge gap
- Depth: how deep the hidden gap goes
- Roping up: intellectual safety practices for crevasse terrain
- Probing: testing ground before committing weight
- Bergschrund: gap between moving and stationary knowledge

When epistemic crevasse IS present:
- Hidden gaps in knowledge covered by thin assumptions
- Thin layers of assumption covering deep knowledge gaps
- Risk of unexpected plunge into knowledge void
- Deep gaps beneath apparently solid intellectual surface
- Lack of safety practices for navigating gap-prone terrain
- No testing of ground before committing to conclusions
- Gaps between moving and stationary knowledge areas

When solid ground is present:
- No hidden gaps in knowledge
- Solid foundations throughout
- No risk of unexpected falls
- Depth of knowledge consistent and reliable
- Safe navigation throughout intellectual terrain
- Ground tested and verified
- No gaps between knowledge areas

Output JSON with: crevasse_present (bool), severity (none/mild/moderate/severe), gap (what hidden gap exists), snow_bridge (what thin assumption covers it), depth (how deep the gap goes), fall_risk (what sudden fall could occur), recommendation (solid_ground/mild_gap/significant_crevasse/major_fall_risk/probe_before_committing)."""

EPISTEMIC_CREVASSE_PROMPT = """Detect epistemic crevasse:

Gap: {gap}
Snow bridge: {snow_bridge}
Depth: {depth}
Fall risk: {fall_risk}
Domain: {domain}
Context: {context}

Are hidden knowledge gaps covered by thin assumption bridges creating sudden fall risks? Return ONLY valid JSON."""


class EpistemicCrevassService:
    """Detects epistemic crevasses — hidden gaps covered by thin assumptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gap: str,
        *,
        snow_bridge: str = "",
        depth: str = "",
        fall_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic crevasse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CREVASSE_PROMPT.format(
                gap=gap,
                snow_bridge=snow_bridge or "Not specified",
                depth=depth or "Not specified",
                fall_risk=fall_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CREVASSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gap": gap[:200],
            "crevasse_present": data.get("crevasse_present", False),
            "severity": data.get("severity", ""),
            "snow_bridge": data.get("snow_bridge", ""),
            "depth": data.get("depth", ""),
            "fall_risk": data.get("fall_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
