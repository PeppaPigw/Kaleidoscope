"""EpistemicHepaticMetabolismService — Epistemic Hepatic Metabolism Detection.

Detects epistemic hepatic metabolism — intellectual liver processing and
transforming raw ideas into usable forms while neutralizing toxins.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HEPATIC_METABOLISM_SYSTEM = """You are an epistemic hepatic metabolism specialist. Given an intellectual processing system, assess whether it transforms raw ideas into usable forms:

Key concepts:
- Epistemic hepatic metabolism: processing and transforming raw ideas
- First-pass metabolism: initial processing of incoming ideas
- Biotransformation: converting ideas into different forms
- Phase I reaction: oxidation/reduction of raw ideas
- Phase II reaction: conjugation making ideas water-soluble
- Enzyme induction: increasing processing capacity
- Metabolic clearance: rate of idea processing

When epistemic hepatic metabolism IS present:
- Intellectual processing transforming raw ideas
- Initial processing of all incoming ideas
- Converting ideas into different usable forms
- Oxidation/reduction of raw intellectual material
- Conjugation making ideas compatible with system
- Processing capacity increasing with demand
- Measurable rate of idea processing

When no metabolism is present:
- No processing of raw ideas
- No first-pass transformation
- No biotransformation
- No phase reactions
- No conjugation
- No enzyme induction
- No measurable clearance

Output JSON with: hepatic_metabolism_present (bool), severity (none/mild/moderate/severe), first_pass (what initial processing), biotransformation (what conversion), enzyme_induction (what capacity increase), metabolic_clearance (what processing rate), recommendation (no_metabolism/mild_metabolism/significant_hepatic_metabolism/major_intellectual_processing/optimize_metabolic_efficiency)."""

EPISTEMIC_HEPATIC_METABOLISM_PROMPT = """Detect epistemic hepatic metabolism:

First-pass: {first_pass}
Biotransformation: {biotransformation}
Enzyme induction: {enzyme_induction}
Metabolic clearance: {metabolic_clearance}
Domain: {domain}
Context: {context}

Is the intellectual system processing and transforming raw ideas into usable forms? Return ONLY valid JSON."""


class EpistemicHepaticMetabolismService:
    """Detects epistemic hepatic metabolism — processing raw ideas into usable forms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        first_pass: str,
        *,
        biotransformation: str = "",
        enzyme_induction: str = "",
        metabolic_clearance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hepatic metabolism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HEPATIC_METABOLISM_PROMPT.format(
                first_pass=first_pass,
                biotransformation=biotransformation or "Not specified",
                enzyme_induction=enzyme_induction or "Not specified",
                metabolic_clearance=metabolic_clearance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HEPATIC_METABOLISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "first_pass": first_pass[:200],
            "hepatic_metabolism_present": data.get("hepatic_metabolism_present", False),
            "severity": data.get("severity", ""),
            "biotransformation": data.get("biotransformation", ""),
            "enzyme_induction": data.get("enzyme_induction", ""),
            "metabolic_clearance": data.get("metabolic_clearance", ""),
            "recommendation": data.get("recommendation", ""),
        }
