"""EpistemicNarrativeVillainService — Epistemic Narrative Villain Bias Detection.

Detects epistemic narrative villain bias — casting others as villains
to simplify complex situations into good-vs-evil narratives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_VILLAIN_SYSTEM = """You are an epistemic narrative villain bias specialist. Given villain-casting that simplifies complex situations, assess villain bias:

Key concepts:
- Epistemic narrative villain bias: casting others as villains to simplify complexity
- Othering: reducing complex actors to simple antagonists
- Evil attribution: attributing malice where incompetence or complexity suffices
- Moral simplification: simplifying moral complexity into good vs evil
- Scapegoating: blaming specific actors for systemic issues
- Dehumanization: reducing others' humanity to fit villain role
- Conspiracy framing: framing complex events as villain-driven plots

When epistemic narrative villain bias IS present:
- Others cast as villains
- Complex actors reduced to antagonists
- Malice attributed without evidence
- Moral complexity simplified
- Scapegoats identified
- Others dehumanized
- Events framed as plots

When no villain bias:
- Others seen as complex agents
- Multiple motivations considered
- Incompetence/complexity considered before malice
- Moral complexity preserved
- Systemic causes examined
- Others' humanity preserved
- Events seen as emergent not plotted

Output JSON with: narrative_villain_detected (bool), severity (none/mild/moderate/severe), othering (who othered and how), evil_attribution (what malice attributed), moral_simplification (what simplified), scapegoating (who scapegoated), recommendation (no_narrative_villain/mild_complexity_practice/significant_empathy_recovery/major_intensive_devillainization/emergency_complete_villain_bias)."""

EPISTEMIC_NARRATIVE_VILLAIN_PROMPT = """Detect epistemic narrative villain bias:

Othering: {othering}
Evil attribution: {evil_attribution}
Moral simplification: {moral_simplification}
Scapegoating: {scapegoating}
Domain: {domain}
Context: {context}

Are others being cast as villains to simplify complex situations? Return ONLY valid JSON."""


class EpistemicNarrativeVillainService:
    """Detects epistemic narrative villain bias — others as antagonists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        othering: str,
        *,
        evil_attribution: str = "",
        moral_simplification: str = "",
        scapegoating: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative villain bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_VILLAIN_PROMPT.format(
                othering=othering,
                evil_attribution=evil_attribution or "Not specified",
                moral_simplification=moral_simplification or "Not specified",
                scapegoating=scapegoating or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_VILLAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "othering": othering[:200],
            "narrative_villain_detected": data.get("narrative_villain_detected", False),
            "severity": data.get("severity", ""),
            "evil_attribution": data.get("evil_attribution", ""),
            "moral_simplification": data.get("moral_simplification", ""),
            "scapegoating": data.get("scapegoating", ""),
            "recommendation": data.get("recommendation", ""),
        }
