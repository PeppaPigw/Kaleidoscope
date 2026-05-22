"""EpistemicPerpetualMotionService — Epistemic Perpetual Motion Detection.

Detects epistemic perpetual motion — claims of self-sustaining
arguments that require no external evidence or energy input.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERPETUAL_MOTION_SYSTEM = """You are an epistemic perpetual motion specialist. Given an argument pattern, assess whether it claims self-sustaining validity without evidence input:

Key concepts:
- Epistemic perpetual motion: arguments claiming to sustain themselves without evidence
- Self-referential validity: arguments that validate themselves
- No external input: claims requiring no external evidence
- Circular energy: energy coming from the argument itself
- Impossible machine: intellectual machine that violates epistemic laws
- Free lunch: getting conclusions without paying evidence cost
- Closed system: system claiming to generate knowledge from nothing

When perpetual motion IS present:
- Arguments claiming to sustain themselves without evidence
- Self-referential validation without external check
- Claims requiring no external evidence input
- Intellectual energy supposedly coming from nowhere
- Intellectual machine violating basic epistemic principles
- Getting conclusions without paying evidence cost
- Closed system claiming to generate knowledge from nothing

When properly powered argument is present:
- Arguments sustained by external evidence
- Validation from independent sources
- Claims supported by external evidence
- Intellectual energy from legitimate sources
- Arguments following basic epistemic principles
- Conclusions proportionate to evidence invested
- Open system drawing on external knowledge

Output JSON with: perpetual_motion (bool), severity (none/mild/moderate/severe), argument (what argument claims self-sustenance), self_reference (how it references itself), missing_input (what external input is missing), impossibility (why it cannot work), recommendation (properly_powered/mild_circularity/significant_perpetual_motion/major_epistemic_violation/provide_external_evidence)."""

EPISTEMIC_PERPETUAL_MOTION_PROMPT = """Detect epistemic perpetual motion:

Argument: {argument}
Self reference: {self_reference}
Missing input: {missing_input}
Impossibility: {impossibility}
Domain: {domain}
Context: {context}

Does this argument claim to sustain itself without external evidence input? Return ONLY valid JSON."""


class EpistemicPerpetualMotionService:
    """Detects epistemic perpetual motion — self-sustaining argument claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        self_reference: str = "",
        missing_input: str = "",
        impossibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic perpetual motion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERPETUAL_MOTION_PROMPT.format(
                argument=argument,
                self_reference=self_reference or "Not specified",
                missing_input=missing_input or "Not specified",
                impossibility=impossibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERPETUAL_MOTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "perpetual_motion": data.get("perpetual_motion", False),
            "severity": data.get("severity", ""),
            "self_reference": data.get("self_reference", ""),
            "missing_input": data.get("missing_input", ""),
            "impossibility": data.get("impossibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
