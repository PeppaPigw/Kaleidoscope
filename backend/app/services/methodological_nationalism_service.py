"""MethodologicalNationalismService — Methodological Nationalism Detection.

Detects methodological nationalism — unconsciously treating the
nation-state as the natural unit of analysis when other scales
(local, regional, global, network) may be more appropriate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

METHODOLOGICAL_NATIONALISM_SYSTEM = """You are a methodological nationalism specialist. Given an analysis, assess whether the nation-state is being treated as the natural unit of analysis inappropriately:

Key concepts:
- Methodological nationalism: nation-state as default analytical unit
- Container thinking: treating nations as bounded containers
- Scale fixation: analyzing at one scale when another is more appropriate
- Territorial trap: assuming social processes are bounded by borders
- Naturalization of borders: treating political boundaries as natural
- Scalar mismatch: phenomenon operates at different scale than analysis
- Wimmer-Glick Schiller critique: social science's national bias

When methodological nationalism IS present:
- Nation-state used as unit of analysis without justification
- Phenomena that cross borders analyzed within national frames
- Political boundaries treated as natural analytical boundaries
- Sub-national or supra-national patterns invisible
- Comparison only between nations, not other units
- National statistics used for non-national phenomena
- Borders assumed to bound social processes

When national-level analysis is appropriate:
- Phenomenon genuinely operates at national level
- National institutions are the relevant causal factor
- Scale choice justified explicitly
- Limitations of national frame acknowledged
- Cross-border dynamics noted where relevant
- Multiple scales considered
- National frame chosen deliberately, not by default

Output JSON with: nationalism_present (bool), severity (none/mild/moderate/severe), analysis (what is analyzed), assumed_unit (what unit is assumed), better_scale (what scale might be more appropriate), invisible_patterns (what patterns are missed), recommendation (appropriate_national_frame/mild_scale_assumption/significant_methodological_nationalism/major_territorial_trap/consider_alternative_scales)."""

METHODOLOGICAL_NATIONALISM_PROMPT = """Detect methodological nationalism:

Analysis: {analysis}
Unit of analysis: {unit}
Phenomenon: {phenomenon}
Scale: {scale}
Domain: {domain}
Context: {context}

Is the nation-state being treated as the natural unit of analysis inappropriately? Return ONLY valid JSON."""


class MethodologicalNationalismService:
    """Detects methodological nationalism — nation-state as default analytical unit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        unit: str = "",
        phenomenon: str = "",
        scale: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect methodological nationalism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METHODOLOGICAL_NATIONALISM_PROMPT.format(
                analysis=analysis,
                unit=unit or "Not specified",
                phenomenon=phenomenon or "Not specified",
                scale=scale or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=METHODOLOGICAL_NATIONALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "nationalism_present": data.get("nationalism_present", False),
            "severity": data.get("severity", ""),
            "assumed_unit": data.get("assumed_unit", ""),
            "better_scale": data.get("better_scale", ""),
            "invisible_patterns": data.get("invisible_patterns", ""),
            "recommendation": data.get("recommendation", ""),
        }
