"""EpistemicDenialOfServiceService — Epistemic Denial of Service Detection.

Detects epistemic denial of service — overwhelming someone's epistemic
capacity to prevent them from functioning effectively.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOS_SYSTEM = """You are an epistemic denial of service specialist. Given a discourse situation, assess whether someone's epistemic capacity is being deliberately overwhelmed:

Key concepts:
- Epistemic denial of service: overwhelming epistemic capacity
- Information flooding: flooding with information to prevent processing
- Attention exhaustion: exhausting attention to prevent focus
- Cognitive overload attack: deliberately overloading cognitive resources
- Decision fatigue weaponization: creating decision fatigue deliberately
- Complexity bombing: using complexity to overwhelm
- Epistemic resource exhaustion: exhausting epistemic resources

When epistemic denial of service IS present:
- Epistemic capacity deliberately overwhelmed
- Information flooding preventing processing
- Attention exhausted to prevent focus
- Cognitive resources deliberately overloaded
- Decision fatigue created strategically
- Complexity used to overwhelm not inform
- Epistemic resources exhausted by design

When high information load is present:
- Information volume proportionate to topic complexity
- Attention demands reasonable for the subject
- Cognitive load inherent to the material
- Decision complexity reflecting genuine options
- Complexity reflecting genuine difficulty
- Resources demanded proportionate to importance

Output JSON with: dos_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), overload_method (how overload is created), target_capacity (what capacity is targeted), strategic_purpose (what purpose overload serves), recommendation (proportionate_load/mild_overload/significant_epistemic_dos/major_capacity_attack/respect_epistemic_capacity)."""

EPISTEMIC_DOS_PROMPT = """Detect epistemic denial of service:

Situation: {situation}
Overload method: {method}
Target capacity: {target}
Purpose: {purpose}
Domain: {domain}
Context: {context}

Is someone's epistemic capacity being deliberately overwhelmed? Return ONLY valid JSON."""


class EpistemicDenialOfServiceService:
    """Detects epistemic denial of service — overwhelming epistemic capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        method: str = "",
        target: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic denial of service."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOS_PROMPT.format(
                situation=situation,
                method=method or "Not specified",
                target=target or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "dos_present": data.get("dos_present", False),
            "severity": data.get("severity", ""),
            "overload_method": data.get("overload_method", ""),
            "target_capacity": data.get("target_capacity", ""),
            "strategic_purpose": data.get("strategic_purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
