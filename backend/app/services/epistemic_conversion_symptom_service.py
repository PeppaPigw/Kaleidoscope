"""EpistemicConversionSymptomService — Epistemic Conversion Symptom Detection.

Detects epistemic conversion symptoms — intellectual conflict converted into
functional impairment that prevents engagement with the conflicted material.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONVERSION_SYMPTOM_SYSTEM = """You are an epistemic conversion symptom specialist. Given intellectual conflict becoming functional impairment, assess conversion:

Key concepts:
- Epistemic conversion symptom: conflict becoming impairment
- La belle indifference: unconcerned about the impairment
- Symbolic meaning: impairment symbolizes the conflict
- Primary gain: conflict removed from awareness
- Functional specificity: impairment targets specific capacity
- Neurological impossibility: impairment doesn't follow neural logic
- Conflict resolution: symptom resolves the impossible choice

When epistemic conversion symptom IS present:
- Conflict becoming impairment
- Unconcerned about impairment
- Impairment symbolizes conflict
- Conflict removed from awareness
- Targets specific capacity
- Doesn't follow logic
- Symptom resolves choice

When no conversion symptom:
- Conflict faced directly
- Appropriate concern
- No symbolic impairment
- Conflict in awareness
- Full capacity available
- Logical functioning
- Direct resolution

Output JSON with: conversion_symptom_detected (bool), severity (none/mild/moderate/severe), symbolic_meaning (what symbolizing), primary_gain (what removing from awareness), functional_specificity (what targeting), conflict_resolution (what resolving), recommendation (no_conversion_symptom/mild_conflict_awareness/significant_conversion_therapy/major_intensive_psychodynamic_work/emergency_severe_impairment)."""

EPISTEMIC_CONVERSION_SYMPTOM_PROMPT = """Detect epistemic conversion symptom:

Symbolic meaning: {symbolic_meaning}
Primary gain: {primary_gain}
Functional specificity: {functional_specificity}
Conflict resolution: {conflict_resolution}
Domain: {domain}
Context: {context}

Is intellectual conflict being converted into functional impairment? Return ONLY valid JSON."""


class EpistemicConversionSymptomService:
    """Detects epistemic conversion symptoms — conflict becoming impairment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symbolic_meaning: str,
        *,
        primary_gain: str = "",
        functional_specificity: str = "",
        conflict_resolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conversion symptom."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONVERSION_SYMPTOM_PROMPT.format(
                symbolic_meaning=symbolic_meaning,
                primary_gain=primary_gain or "Not specified",
                functional_specificity=functional_specificity or "Not specified",
                conflict_resolution=conflict_resolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONVERSION_SYMPTOM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symbolic_meaning": symbolic_meaning[:200],
            "conversion_symptom_detected": data.get("conversion_symptom_detected", False),
            "severity": data.get("severity", ""),
            "primary_gain": data.get("primary_gain", ""),
            "functional_specificity": data.get("functional_specificity", ""),
            "conflict_resolution": data.get("conflict_resolution", ""),
            "recommendation": data.get("recommendation", ""),
        }
