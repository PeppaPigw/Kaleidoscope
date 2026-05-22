"""EpistemicSedationService — Epistemic Sedation Detection.

Detects epistemic sedation — intellectual systems being artificially
suppressed or numbed, reducing awareness and responsiveness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SEDATION_SYSTEM = """You are an epistemic sedation specialist. Given intellectual suppression, assess whether sedation is occurring:

Key concepts:
- Epistemic sedation: artificial suppression of intellectual awareness
- Oversedation: excessive suppression beyond therapeutic need
- Undersedation: insufficient suppression causing distress
- Sedation vacation: periodic awakening to assess function
- Delirium: confused state from sedation effects
- Richmond scale: measuring depth of sedation
- Propofol infusion: continuous suppression delivery

When epistemic sedation IS occurring:
- Intellectual awareness artificially suppressed
- Excessive suppression beyond need
- Insufficient suppression causing distress
- No periodic awakening assessment
- Confused state from suppression
- Deep sedation without monitoring
- Continuous suppression without breaks

When no sedation present:
- Normal intellectual awareness
- No artificial suppression
- No distress requiring suppression
- Regular awareness assessment
- Clear intellectual state
- Appropriate alertness level
- Natural intellectual rhythm

Output JSON with: sedation_detected (bool), severity (none/mild/moderate/severe), sedation_depth (what suppression level), oversedation_risk (what excess suppression), delirium_signs (what confusion present), awakening_protocol (what assessment plan), recommendation (no_sedation_detected/mild_suppression/significant_sedation/major_oversedation/emergency_sedation_crisis)."""

EPISTEMIC_SEDATION_PROMPT = """Detect epistemic sedation:

Sedation depth: {sedation_depth}
Oversedation risk: {oversedation_risk}
Delirium signs: {delirium_signs}
Awakening protocol: {awakening_protocol}
Domain: {domain}
Context: {context}

Is intellectual awareness being artificially suppressed? Return ONLY valid JSON."""


class EpistemicSedationService:
    """Detects epistemic sedation — artificial suppression of intellectual awareness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        sedation_depth: str,
        *,
        oversedation_risk: str = "",
        delirium_signs: str = "",
        awakening_protocol: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sedation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SEDATION_PROMPT.format(
                sedation_depth=sedation_depth,
                oversedation_risk=oversedation_risk or "Not specified",
                delirium_signs=delirium_signs or "Not specified",
                awakening_protocol=awakening_protocol or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SEDATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "sedation_depth": sedation_depth[:200],
            "sedation_detected": data.get("sedation_detected", False),
            "severity": data.get("severity", ""),
            "oversedation_risk": data.get("oversedation_risk", ""),
            "delirium_signs": data.get("delirium_signs", ""),
            "awakening_protocol": data.get("awakening_protocol", ""),
            "recommendation": data.get("recommendation", ""),
        }
