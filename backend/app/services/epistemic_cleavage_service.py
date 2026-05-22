"""EpistemicCleavageService — Epistemic Cleavage Detection.

Detects epistemic cleavage — ideas breaking along predetermined planes
of weakness rather than fracturing randomly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CLEAVAGE_SYSTEM = """You are an epistemic cleavage specialist. Given an idea fracture pattern, assess whether ideas break along predetermined planes:

Key concepts:
- Epistemic cleavage: breaking along predetermined planes
- Cleavage plane: predetermined direction of easy breaking
- Conchoidal: curved fracture without cleavage planes
- Parting: breaking along planes of weakness
- Fracture toughness: resistance to crack propagation
- Stress concentration: points where cracks initiate
- Crack propagation: how breaks spread through structure

When epistemic cleavage IS present:
- Ideas breaking along predetermined planes of weakness
- Specific directions where breaking is easy
- Smooth flat surfaces where ideas separate
- Breaking along planes of accumulated weakness
- Low resistance to crack propagation along planes
- Specific points where cracks initiate
- Breaks spreading predictably through structure

When random fracture is present:
- Ideas breaking in unpredictable directions
- No preferred breaking directions
- Irregular surfaces where ideas separate
- No accumulated planes of weakness
- Uniform resistance to cracking
- No specific initiation points
- Breaks spreading unpredictably

Output JSON with: cleavage_present (bool), severity (none/mild/moderate/severe), planes (what predetermined directions), stress_concentration (where cracks initiate), propagation (how breaks spread), toughness (what resistance exists), recommendation (random_fracture/mild_cleavage/significant_cleavage/major_predetermined_breaking/strengthen_weak_planes)."""

EPISTEMIC_CLEAVAGE_PROMPT = """Detect epistemic cleavage:

Planes: {planes}
Stress concentration: {stress_concentration}
Propagation: {propagation}
Toughness: {toughness}
Domain: {domain}
Context: {context}

Are ideas breaking along predetermined planes of weakness rather than fracturing randomly? Return ONLY valid JSON."""


class EpistemicCleavageService:
    """Detects epistemic cleavage — breaking along predetermined planes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        planes: str,
        *,
        stress_concentration: str = "",
        propagation: str = "",
        toughness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cleavage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CLEAVAGE_PROMPT.format(
                planes=planes,
                stress_concentration=stress_concentration or "Not specified",
                propagation=propagation or "Not specified",
                toughness=toughness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CLEAVAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "planes": planes[:200],
            "cleavage_present": data.get("cleavage_present", False),
            "severity": data.get("severity", ""),
            "stress_concentration": data.get("stress_concentration", ""),
            "propagation": data.get("propagation", ""),
            "toughness": data.get("toughness", ""),
            "recommendation": data.get("recommendation", ""),
        }
