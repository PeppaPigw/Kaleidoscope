"""EpistemicAbstractionEscapeService — Epistemic Abstraction Escape Detection.

Detects epistemic abstraction escape — fleeing to abstraction
to avoid concrete accountability or uncomfortable specifics.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABSTRACTION_ESCAPE_SYSTEM = """You are an epistemic abstraction escape specialist. Given fleeing to abstraction to avoid accountability, assess abstraction escape:

Key concepts:
- Epistemic abstraction escape: fleeing to abstraction to avoid concrete accountability
- Vagueness as shield: using vague language to avoid commitment
- Generality retreat: retreating to generalities when specifics are demanded
- Principle hiding: hiding behind principles to avoid concrete action
- Theory refuge: taking refuge in theory to avoid practice
- Conceptual evasion: evading through conceptual complexity
- Abstract deflection: deflecting concrete questions with abstract answers

When epistemic abstraction escape IS present:
- Fleeing to abstraction when pressed
- Vagueness used as shield
- Retreating to generalities
- Hiding behind principles
- Taking refuge in theory
- Evading through concepts
- Deflecting with abstractions

When no abstraction escape:
- Concrete when needed
- Specific when pressed
- Generalities grounded in specifics
- Principles connected to action
- Theory connected to practice
- Concepts clarify rather than obscure
- Abstract and concrete balanced

Output JSON with: abstraction_escape_detected (bool), severity (none/mild/moderate/severe), vagueness_shield (what vagueness shields), generality_retreat (what retreated from), principle_hiding (what principles hide behind), theory_refuge (what theory used as refuge), recommendation (no_abstraction_escape/mild_concreteness_practice/significant_specificity_recovery/major_intensive_grounding/emergency_complete_abstraction_escape)."""

EPISTEMIC_ABSTRACTION_ESCAPE_PROMPT = """Detect epistemic abstraction escape:

Vagueness shield: {vagueness_shield}
Generality retreat: {generality_retreat}
Principle hiding: {principle_hiding}
Theory refuge: {theory_refuge}
Domain: {domain}
Context: {context}

Is there fleeing to abstraction to avoid concrete accountability? Return ONLY valid JSON."""


class EpistemicAbstractionEscapeService:
    """Detects epistemic abstraction escape — fleeing to vagueness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        vagueness_shield: str,
        *,
        generality_retreat: str = "",
        principle_hiding: str = "",
        theory_refuge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic abstraction escape."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABSTRACTION_ESCAPE_PROMPT.format(
                vagueness_shield=vagueness_shield,
                generality_retreat=generality_retreat or "Not specified",
                principle_hiding=principle_hiding or "Not specified",
                theory_refuge=theory_refuge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABSTRACTION_ESCAPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "vagueness_shield": vagueness_shield[:200],
            "abstraction_escape_detected": data.get("abstraction_escape_detected", False),
            "severity": data.get("severity", ""),
            "generality_retreat": data.get("generality_retreat", ""),
            "principle_hiding": data.get("principle_hiding", ""),
            "theory_refuge": data.get("theory_refuge", ""),
            "recommendation": data.get("recommendation", ""),
        }
