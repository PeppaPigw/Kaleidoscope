"""EpistemicCrohnService — Epistemic Crohn's Disease Detection.

Detects epistemic Crohn's disease — chronic inflammatory disease affecting
any part of the intellectual processing tract with skip lesions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CROHN_SYSTEM = """You are an epistemic Crohn's specialist. Given chronic intellectual tract inflammation, assess Crohn's:

Key concepts:
- Epistemic Crohn's: chronic inflammation of processing tract
- Skip lesions: inflammation in patches with healthy areas between
- Transmural: inflammation through full thickness of tract wall
- Fistula: abnormal connections between tract segments
- Stricture: narrowing from chronic inflammation
- Remission-relapse: cycling between active and quiet periods
- Biologic therapy: targeted immune modulation

When epistemic Crohn's IS present:
- Chronic inflammation of processing tract
- Patchy inflammation with healthy areas between
- Full-thickness tract wall involvement
- Abnormal connections between segments
- Narrowing from chronic inflammation
- Cycling between active and quiet periods
- Targeted modulation needed

When no Crohn's:
- No chronic tract inflammation
- No patchy lesions
- Normal tract wall
- No abnormal connections
- No narrowing
- Stable processing
- No modulation needed

Output JSON with: crohn_detected (bool), severity (none/mild/moderate/severe), inflammation_pattern (what skip lesions), depth (what transmural involvement), complications (what fistula/stricture), disease_activity (what remission status), recommendation (no_crohn/mild_aminosalicylate/significant_immunomodulator/major_biologic/emergency_acute_obstruction)."""

EPISTEMIC_CROHN_PROMPT = """Detect epistemic Crohn's disease:

Inflammation pattern: {inflammation_pattern}
Depth: {depth}
Complications: {complications}
Disease activity: {disease_activity}
Domain: {domain}
Context: {context}

Is there chronic inflammatory disease affecting the intellectual processing tract? Return ONLY valid JSON."""


class EpistemicCrohnService:
    """Detects epistemic Crohn's — chronic inflammation of processing tract."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inflammation_pattern: str,
        *,
        depth: str = "",
        complications: str = "",
        disease_activity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Crohn's disease."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CROHN_PROMPT.format(
                inflammation_pattern=inflammation_pattern,
                depth=depth or "Not specified",
                complications=complications or "Not specified",
                disease_activity=disease_activity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CROHN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inflammation_pattern": inflammation_pattern[:200],
            "crohn_detected": data.get("crohn_detected", False),
            "severity": data.get("severity", ""),
            "depth": data.get("depth", ""),
            "complications": data.get("complications", ""),
            "disease_activity": data.get("disease_activity", ""),
            "recommendation": data.get("recommendation", ""),
        }
