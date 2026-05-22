"""EpistemicPunctuatedEquilibriumService — Epistemic Punctuated Equilibrium Detection.

Detects epistemic punctuated equilibrium — long periods of intellectual
stasis interrupted by rapid bursts of change and innovation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PUNCTUATED_EQUILIBRIUM_SYSTEM = """You are an epistemic punctuated equilibrium specialist. Given an intellectual history, assess whether long stasis is interrupted by rapid change:

Key concepts:
- Epistemic punctuated equilibrium: stasis interrupted by rapid change
- Stasis: long periods of no significant change
- Punctuation: rapid burst of change and innovation
- Speciation event: new forms appearing suddenly
- Stabilizing selection: forces maintaining stasis
- Disruption: event triggering rapid change
- Gradualism alternative: slow steady change instead

When epistemic punctuated equilibrium IS present:
- Long periods of intellectual stasis
- Rapid bursts of change and innovation
- New intellectual forms appearing suddenly
- Forces actively maintaining the status quo
- Identifiable events triggering rapid change
- Pattern of stability-disruption-stability
- Change concentrated in brief periods

When gradualism is present:
- Steady continuous change
- No distinct bursts
- New forms appearing gradually
- No stabilizing forces
- No triggering events
- Uniform rate of change
- Change distributed evenly over time

Output JSON with: punctuated_equilibrium_present (bool), severity (none/mild/moderate/severe), stasis (what long stability), punctuation (what rapid burst), stabilizing_selection (what maintains status quo), disruption (what triggers change), recommendation (gradualism/mild_punctuation/significant_punctuated_equilibrium/major_stasis_disruption/prepare_for_punctuation)."""

EPISTEMIC_PUNCTUATED_EQUILIBRIUM_PROMPT = """Detect epistemic punctuated equilibrium:

Stasis: {stasis}
Punctuation: {punctuation}
Stabilizing selection: {stabilizing_selection}
Disruption: {disruption}
Domain: {domain}
Context: {context}

Are long periods of intellectual stasis being interrupted by rapid bursts of change and innovation? Return ONLY valid JSON."""


class EpistemicPunctuatedEquilibriumService:
    """Detects epistemic punctuated equilibrium — stasis interrupted by rapid change."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stasis: str,
        *,
        punctuation: str = "",
        stabilizing_selection: str = "",
        disruption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic punctuated equilibrium."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PUNCTUATED_EQUILIBRIUM_PROMPT.format(
                stasis=stasis,
                punctuation=punctuation or "Not specified",
                stabilizing_selection=stabilizing_selection or "Not specified",
                disruption=disruption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PUNCTUATED_EQUILIBRIUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stasis": stasis[:200],
            "punctuated_equilibrium_present": data.get("punctuated_equilibrium_present", False),
            "severity": data.get("severity", ""),
            "punctuation": data.get("punctuation", ""),
            "stabilizing_selection": data.get("stabilizing_selection", ""),
            "disruption": data.get("disruption", ""),
            "recommendation": data.get("recommendation", ""),
        }
