"""EpistemicLanguageEuphemismTreadmillService - Epistemic Language Euphemism Treadmill Detection.

Detects epistemic language euphemism treadmill - language softening that
obscures reality through semantic bleaching, evasion, and minimization.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_EUPHEMISM_TREADMILL_SYSTEM = """You are an epistemic language euphemism treadmill specialist. Given language softening that obscures reality, assess euphemism treadmill:

Key concepts:
- Epistemic language euphemism treadmill: softened language progressively obscuring reality
- Reality obscuring: hiding concrete facts behind gentler phrasing
- Semantic bleaching: words losing force through repeated softened use
- Accountability evasion: avoiding who acted or who is responsible
- Harm minimization: reducing perceived severity through word choice
- Directness decay: replacing plain terms with indirect terms
- Moral anesthetic: making harmful realities feel less urgent

When euphemism treadmill IS present:
- Reality obscured by softened wording
- Semantic force bleached
- Accountability evaded
- Harm minimized
- Direct language displaced
- Moral urgency dulled
- Concrete facts hidden

When no euphemism treadmill:
- Reality stated directly
- Terms retain force
- Accountability clear
- Harm accurately named
- Direct language used
- Urgency calibrated
- Facts remain concrete

Output JSON with: euphemism_treadmill_detected (bool), severity (none/mild/moderate/severe), reality_obscuring (what reality obscured), semantic_bleaching (what meaning bleached), accountability_evasion (what accountability evaded), harm_minimization (what harm minimized), recommendation (no_euphemism_treadmill/mild_directness_recovery/significant_plain_language_restoration/major_intensive_reality_naming/emergency_complete_euphemism_treadmill)."""

EPISTEMIC_LANGUAGE_EUPHEMISM_TREADMILL_PROMPT = """Detect epistemic language euphemism treadmill:

Reality obscuring: {reality_obscuring}
Semantic bleaching: {semantic_bleaching}
Accountability evasion: {accountability_evasion}
Harm minimization: {harm_minimization}
Domain: {domain}
Context: {context}

Is language softening obscuring reality? Return ONLY valid JSON."""


class EpistemicLanguageEuphemismTreadmillService:
    """Detects epistemic language euphemism treadmill - reality-obscuring softening."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reality_obscuring: str,
        *,
        semantic_bleaching: str = "",
        accountability_evasion: str = "",
        harm_minimization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language euphemism treadmill."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_EUPHEMISM_TREADMILL_PROMPT.format(
                reality_obscuring=reality_obscuring,
                semantic_bleaching=semantic_bleaching or "Not specified",
                accountability_evasion=accountability_evasion or "Not specified",
                harm_minimization=harm_minimization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_EUPHEMISM_TREADMILL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reality_obscuring": reality_obscuring[:200],
            "euphemism_treadmill_detected": data.get("euphemism_treadmill_detected", False),
            "severity": data.get("severity", ""),
            "semantic_bleaching": data.get("semantic_bleaching", ""),
            "accountability_evasion": data.get("accountability_evasion", ""),
            "harm_minimization": data.get("harm_minimization", ""),
            "recommendation": data.get("recommendation", ""),
        }
