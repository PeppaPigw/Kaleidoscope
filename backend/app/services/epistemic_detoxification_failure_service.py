"""EpistemicDetoxificationFailureService — Epistemic Detoxification Failure Detection.

Detects epistemic detoxification failure — inability to neutralize harmful
intellectual substances, allowing toxins to accumulate in the system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DETOXIFICATION_FAILURE_SYSTEM = """You are an epistemic detoxification failure specialist. Given an intellectual detox system, assess whether it fails to neutralize harmful substances:

Key concepts:
- Epistemic detoxification failure: inability to neutralize harmful ideas
- Toxic accumulation: harmful substances building up
- Enzyme deficiency: lacking processing machinery
- Metabolic overload: too many toxins for capacity
- Hepatotoxicity: processing system damaged by toxins
- Conjugation failure: inability to make toxins excretable
- Bioactivation: processing making substances more toxic

When epistemic detoxification failure IS present:
- Inability to neutralize harmful intellectual substances
- Harmful ideas building up in the system
- Lacking machinery to process toxic ideas
- Too many toxic ideas for processing capacity
- Processing system itself damaged by toxins
- Inability to make toxic ideas excretable
- Processing accidentally making ideas more harmful

When healthy detox is present:
- Effective neutralization of harmful substances
- No toxic accumulation
- Adequate processing machinery
- Capacity matching demand
- Processing system healthy
- Successful conjugation and excretion
- No bioactivation problems

Output JSON with: detoxification_failure_present (bool), severity (none/mild/moderate/severe), toxic_accumulation (what buildup), enzyme_deficiency (what lacking machinery), metabolic_overload (what capacity exceeded), hepatotoxicity (what processing damage), recommendation (healthy_detox/mild_failure/significant_detoxification_failure/major_toxic_accumulation/restore_detox_capacity)."""

EPISTEMIC_DETOXIFICATION_FAILURE_PROMPT = """Detect epistemic detoxification failure:

Toxic accumulation: {toxic_accumulation}
Enzyme deficiency: {enzyme_deficiency}
Metabolic overload: {metabolic_overload}
Hepatotoxicity: {hepatotoxicity}
Domain: {domain}
Context: {context}

Is the intellectual system failing to neutralize harmful substances, allowing toxins to accumulate? Return ONLY valid JSON."""


class EpistemicDetoxificationFailureService:
    """Detects epistemic detoxification failure — inability to neutralize harmful ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        toxic_accumulation: str,
        *,
        enzyme_deficiency: str = "",
        metabolic_overload: str = "",
        hepatotoxicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic detoxification failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DETOXIFICATION_FAILURE_PROMPT.format(
                toxic_accumulation=toxic_accumulation,
                enzyme_deficiency=enzyme_deficiency or "Not specified",
                metabolic_overload=metabolic_overload or "Not specified",
                hepatotoxicity=hepatotoxicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DETOXIFICATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "toxic_accumulation": toxic_accumulation[:200],
            "detoxification_failure_present": data.get("detoxification_failure_present", False),
            "severity": data.get("severity", ""),
            "enzyme_deficiency": data.get("enzyme_deficiency", ""),
            "metabolic_overload": data.get("metabolic_overload", ""),
            "hepatotoxicity": data.get("hepatotoxicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
