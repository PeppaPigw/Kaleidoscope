"""EpistemicConversionService — Epistemic Conversion Disorder Detection.

Detects epistemic conversion disorder — intellectual paralysis or
dysfunction without identifiable organic cause.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONVERSION_SYSTEM = """You are an epistemic conversion disorder specialist. Given intellectual paralysis without cause, assess conversion:

Key concepts:
- Epistemic conversion: intellectual dysfunction without organic cause
- Paralysis: inability to think despite intact capacity
- Blindness: inability to see solutions that are present
- Mutism: inability to express ideas despite having them
- Seizure-like: episodes mimicking intellectual breakdown
- Psychological origin: distress converting to intellectual symptoms
- La belle indifference: unconcerned about dysfunction

When epistemic conversion IS present:
- Dysfunction without organic cause
- Inability despite intact capacity
- Cannot see present solutions
- Cannot express existing ideas
- Episodes mimicking breakdown
- Distress converting to symptoms
- Unconcerned about dysfunction

When no conversion:
- Function matches capacity
- Thinking matches ability
- Seeing available solutions
- Expressing ideas freely
- No pseudo-episodes
- Direct distress expression
- Appropriate concern

Output JSON with: conversion_detected (bool), severity (none/mild/moderate/severe), symptom_type (what dysfunction), organic_absence (what no cause found), psychological_trigger (what distress source), indifference_level (what unconcern), recommendation (no_conversion/mild_psychoeducation/significant_therapy/major_intensive_treatment/emergency_complete_paralysis)."""

EPISTEMIC_CONVERSION_PROMPT = """Detect epistemic conversion disorder:

Symptom type: {symptom_type}
Organic absence: {organic_absence}
Psychological trigger: {psychological_trigger}
Indifference level: {indifference_level}
Domain: {domain}
Context: {context}

Is there intellectual paralysis or dysfunction without identifiable organic cause? Return ONLY valid JSON."""


class EpistemicConversionService:
    """Detects epistemic conversion — dysfunction without organic cause."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symptom_type: str,
        *,
        organic_absence: str = "",
        psychological_trigger: str = "",
        indifference_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conversion disorder."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONVERSION_PROMPT.format(
                symptom_type=symptom_type,
                organic_absence=organic_absence or "Not specified",
                psychological_trigger=psychological_trigger or "Not specified",
                indifference_level=indifference_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONVERSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symptom_type": symptom_type[:200],
            "conversion_detected": data.get("conversion_detected", False),
            "severity": data.get("severity", ""),
            "organic_absence": data.get("organic_absence", ""),
            "psychological_trigger": data.get("psychological_trigger", ""),
            "indifference_level": data.get("indifference_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
