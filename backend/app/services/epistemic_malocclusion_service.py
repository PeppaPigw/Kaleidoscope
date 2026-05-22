"""EpistemicMalocclusionService — Epistemic Malocclusion Detection.

Detects epistemic malocclusion — intellectual concepts not aligning properly,
causing dysfunction in how ideas meet and interact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MALOCCLUSION_SYSTEM = """You are an epistemic malocclusion specialist. Given intellectual alignment problems, assess malocclusion:

Key concepts:
- Epistemic malocclusion: concepts not aligning properly
- Overbite: one set of ideas dominating overlap
- Underbite: subordinate ideas protruding beyond dominant
- Crossbite: lateral misalignment of concept pairs
- Open bite: concepts that should meet but don't
- Orthodontics: gradual realignment over time
- TMJ dysfunction: joint problems from misalignment

When epistemic malocclusion IS present:
- Concepts not aligning properly
- One set dominating overlap
- Subordinate ideas protruding
- Lateral misalignment present
- Concepts that should meet don't
- Gradual realignment needed
- Joint problems from misalignment

When no malocclusion:
- Proper concept alignment
- Balanced overlap
- Normal hierarchy
- Lateral alignment correct
- Concepts meeting properly
- No realignment needed
- No joint dysfunction

Output JSON with: malocclusion_detected (bool), severity (none/mild/moderate/severe), alignment_type (what misalignment), bite_classification (what category), functional_impact (what dysfunction), correction_plan (what realignment), recommendation (no_malocclusion/mild_monitoring/significant_orthodontics/major_surgical_correction/emergency_acute_tmj)."""

EPISTEMIC_MALOCCLUSION_PROMPT = """Detect epistemic malocclusion:

Alignment type: {alignment_type}
Bite classification: {bite_classification}
Functional impact: {functional_impact}
Correction plan: {correction_plan}
Domain: {domain}
Context: {context}

Are intellectual concepts not aligning properly causing dysfunction? Return ONLY valid JSON."""


class EpistemicMalocclusionService:
    """Detects epistemic malocclusion — concepts not aligning properly."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        alignment_type: str,
        *,
        bite_classification: str = "",
        functional_impact: str = "",
        correction_plan: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic malocclusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MALOCCLUSION_PROMPT.format(
                alignment_type=alignment_type,
                bite_classification=bite_classification or "Not specified",
                functional_impact=functional_impact or "Not specified",
                correction_plan=correction_plan or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MALOCCLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "alignment_type": alignment_type[:200],
            "malocclusion_detected": data.get("malocclusion_detected", False),
            "severity": data.get("severity", ""),
            "bite_classification": data.get("bite_classification", ""),
            "functional_impact": data.get("functional_impact", ""),
            "correction_plan": data.get("correction_plan", ""),
            "recommendation": data.get("recommendation", ""),
        }
