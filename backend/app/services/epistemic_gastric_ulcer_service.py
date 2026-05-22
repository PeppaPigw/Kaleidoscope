"""EpistemicGastricUlcerService — Epistemic Gastric Ulcer Detection.

Detects epistemic gastric ulcer — self-digestion of intellectual lining
from excess critical acid eroding protective barriers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GASTRIC_ULCER_SYSTEM = """You are an epistemic gastric ulcer specialist. Given intellectual lining, assess whether self-digestion from excess acid is occurring:

Key concepts:
- Epistemic gastric ulcer: self-digestion from excess critical acid
- Mucosal erosion: protective lining being eaten away
- Acid hypersecretion: excessive critical output
- Helicobacter: persistent irritant weakening defenses
- Perforation: ulcer breaking through completely
- Hemorrhage: bleeding from eroded intellectual vessels
- Proton pump inhibition: reducing acid production

When epistemic gastric ulcer IS present:
- Self-digestion of intellectual lining from excess acid
- Protective barriers being eaten away
- Excessive critical output damaging own tissue
- Persistent irritants weakening intellectual defenses
- Risk of breaking through completely
- Bleeding from eroded intellectual structures
- Need to reduce critical acid production

When healthy lining is present:
- Intact protective lining
- No mucosal erosion
- Balanced acid production
- No persistent irritants
- No perforation risk
- No hemorrhage
- No acid suppression needed

Output JSON with: gastric_ulcer_present (bool), severity (none/mild/moderate/severe), mucosal_erosion (what lining damage), acid_hypersecretion (what excess criticism), helicobacter (what persistent irritant), perforation (what breakthrough risk), recommendation (healthy_lining/mild_ulcer/significant_gastric_ulcer/major_self_digestion/reduce_intellectual_acid)."""

EPISTEMIC_GASTRIC_ULCER_PROMPT = """Detect epistemic gastric ulcer:

Mucosal erosion: {mucosal_erosion}
Acid hypersecretion: {acid_hypersecretion}
Helicobacter: {helicobacter}
Perforation: {perforation}
Domain: {domain}
Context: {context}

Is excess critical acid causing self-digestion of the intellectual lining? Return ONLY valid JSON."""


class EpistemicGastricUlcerService:
    """Detects epistemic gastric ulcer — self-digestion from excess criticism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mucosal_erosion: str,
        *,
        acid_hypersecretion: str = "",
        helicobacter: str = "",
        perforation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gastric ulcer."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GASTRIC_ULCER_PROMPT.format(
                mucosal_erosion=mucosal_erosion,
                acid_hypersecretion=acid_hypersecretion or "Not specified",
                helicobacter=helicobacter or "Not specified",
                perforation=perforation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GASTRIC_ULCER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mucosal_erosion": mucosal_erosion[:200],
            "gastric_ulcer_present": data.get("gastric_ulcer_present", False),
            "severity": data.get("severity", ""),
            "acid_hypersecretion": data.get("acid_hypersecretion", ""),
            "helicobacter": data.get("helicobacter", ""),
            "perforation": data.get("perforation", ""),
            "recommendation": data.get("recommendation", ""),
        }
