"""EpistemicScapegoatingService — Epistemic Scapegoating Detection.

Detects epistemic scapegoating — blaming knowledge failures on
individuals rather than systemic factors, where personal blame
substitutes for understanding structural causes of epistemic failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCAPEGOATING_SYSTEM = """You are an epistemic scapegoating specialist. Given a blame attribution, assess whether individuals are being scapegoated for systemic failures:

Key concepts:
- Epistemic scapegoating: blaming individuals for systemic failures
- Personal blame for structural problems: individual fault for system issues
- System blindness: not seeing systemic causes
- Fundamental attribution error: attributing to person not situation
- Accountability theater: visible blame without fixing systems
- Sacrificial accountability: punishing individuals to avoid reform
- Root cause avoidance: blame substituting for understanding

When epistemic scapegoating IS present:
- Individuals blamed for systemic knowledge failures
- Structural causes ignored in favor of personal blame
- System problems attributed to individual failings
- Accountability focused on persons not processes
- Blame substitutes for understanding root causes
- Punishment of individuals avoids systemic reform
- Pattern of failure attributed to individual incompetence

When individual accountability is appropriate:
- Individual genuinely responsible for specific failure
- Systemic factors considered and ruled out
- Individual had resources and authority to prevent failure
- Accountability proportionate to actual responsibility
- Systemic factors also addressed
- Pattern not repeated across different individuals
- Root causes genuinely individual not structural

Output JSON with: scapegoating_present (bool), severity (none/mild/moderate/severe), situation (what failure occurred), individual_blamed (who is blamed), systemic_factors (what systemic factors exist), root_cause (what actual root cause is), recommendation (appropriate_individual_accountability/mild_attribution_bias/significant_epistemic_scapegoating/major_systemic_blame_avoidance/address_systemic_causes)."""

EPISTEMIC_SCAPEGOATING_PROMPT = """Detect epistemic scapegoating:

Situation: {situation}
Blame attribution: {blame}
Systemic factors: {systemic}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Are individuals being scapegoated for systemic knowledge failures? Return ONLY valid JSON."""


class EpistemicScapegoatingService:
    """Detects epistemic scapegoating — blaming individuals for systemic failures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        blame: str = "",
        systemic: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scapegoating."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCAPEGOATING_PROMPT.format(
                situation=situation,
                blame=blame or "Not specified",
                systemic=systemic or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCAPEGOATING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "scapegoating_present": data.get("scapegoating_present", False),
            "severity": data.get("severity", ""),
            "individual_blamed": data.get("individual_blamed", ""),
            "systemic_factors": data.get("systemic_factors", ""),
            "root_cause": data.get("root_cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
