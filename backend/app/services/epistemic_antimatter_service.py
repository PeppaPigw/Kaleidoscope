"""EpistemicAntimatterService — Epistemic Antimatter Detection.

Detects epistemic antimatter — counter-ideas that annihilate on contact
with their counterparts, releasing energy but destroying both.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANTIMATTER_SYSTEM = """You are an epistemic antimatter specialist. Given an intellectual interaction, assess whether counter-ideas annihilate on contact:

Key concepts:
- Epistemic antimatter: counter-ideas annihilating on contact
- Pair production: idea and counter-idea created from energy
- Annihilation: mutual destruction releasing energy
- CP violation: slight asymmetry favoring one over the other
- Antiparticle: exact opposite with reversed properties
- Positronium: brief bound state before annihilation
- Baryon asymmetry: why more ideas than counter-ideas survive

When epistemic antimatter IS present:
- Counter-ideas that destroy their counterparts on contact
- Ideas and counter-ideas created together from energy
- Mutual destruction releasing intellectual energy
- Slight asymmetry favoring one type over the other
- Exact opposites with reversed intellectual properties
- Brief coexistence before mutual destruction
- Unexplained dominance of one type

When compatible ideas is present:
- No mutual destruction on contact
- Ideas created independently
- Coexistence without annihilation
- No asymmetry between types
- No exact opposites
- Stable coexistence
- Balanced representation

Output JSON with: antimatter_present (bool), severity (none/mild/moderate/severe), pair_production (what joint creation), annihilation (what mutual destruction), cp_violation (what asymmetry), positronium (what brief coexistence), recommendation (compatible_ideas/mild_antimatter/significant_antimatter/major_annihilation/separate_matter_antimatter)."""

EPISTEMIC_ANTIMATTER_PROMPT = """Detect epistemic antimatter:

Pair production: {pair_production}
Annihilation: {annihilation}
CP violation: {cp_violation}
Positronium: {positronium}
Domain: {domain}
Context: {context}

Are counter-ideas annihilating on contact with their counterparts, releasing energy but destroying both? Return ONLY valid JSON."""


class EpistemicAntimatterService:
    """Detects epistemic antimatter — counter-ideas annihilating on contact."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pair_production: str,
        *,
        annihilation: str = "",
        cp_violation: str = "",
        positronium: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic antimatter."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANTIMATTER_PROMPT.format(
                pair_production=pair_production,
                annihilation=annihilation or "Not specified",
                cp_violation=cp_violation or "Not specified",
                positronium=positronium or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANTIMATTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pair_production": pair_production[:200],
            "antimatter_present": data.get("antimatter_present", False),
            "severity": data.get("severity", ""),
            "annihilation": data.get("annihilation", ""),
            "cp_violation": data.get("cp_violation", ""),
            "positronium": data.get("positronium", ""),
            "recommendation": data.get("recommendation", ""),
        }
