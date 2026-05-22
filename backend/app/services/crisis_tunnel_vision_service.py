"""CrisisTunnelVisionService — Crisis Tunnel Vision Detection.

Detects crisis tunnel vision — crisis narrowing attention to the
immediate at the expense of systemic understanding, where urgency
prevents seeing the broader picture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CRISIS_TUNNEL_VISION_SYSTEM = """You are a crisis tunnel vision specialist. Given a crisis response, assess whether urgency is narrowing attention inappropriately:

Key concepts:
- Crisis tunnel vision: urgency narrowing attention
- Immediate dominance: immediate concerns blocking systemic view
- Urgency-importance confusion: urgent treated as most important
- Systemic blindness: crisis preventing systemic understanding
- Short-term fixation: only seeing immediate next steps
- Root cause neglect: treating symptoms because of urgency
- Broader context loss: crisis erasing broader context

When crisis tunnel vision IS present:
- Urgency narrowing attention to immediate only
- Systemic factors invisible due to crisis pressure
- Short-term fixes prioritized over root causes
- Broader context lost in crisis response
- Only immediate next steps visible
- Urgency confused with importance
- Crisis preventing systemic understanding

When crisis focus is appropriate:
- Immediate action genuinely required
- Systemic factors acknowledged even if deferred
- Short-term and long-term distinguished
- Broader context maintained alongside urgency
- Root causes noted for later attention
- Urgency and importance distinguished
- Crisis response includes systemic awareness

Output JSON with: tunnel_vision_present (bool), severity (none/mild/moderate/severe), crisis (what crisis is occurring), immediate_focus (what immediate focus dominates), systemic_neglected (what systemic factors are neglected), root_cause_ignored (what root causes are missed), recommendation (appropriate_crisis_focus/mild_urgency_narrowing/significant_tunnel_vision/major_systemic_blindness/maintain_systemic_awareness_in_crisis)."""

CRISIS_TUNNEL_VISION_PROMPT = """Detect crisis tunnel vision:

Crisis: {crisis}
Response focus: {focus}
Systemic factors: {systemic}
Root causes: {root_causes}
Domain: {domain}
Context: {context}

Is crisis urgency narrowing attention at the expense of systemic understanding? Return ONLY valid JSON."""


class CrisisTunnelVisionService:
    """Detects crisis tunnel vision — urgency narrowing attention inappropriately."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        crisis: str,
        *,
        focus: str = "",
        systemic: str = "",
        root_causes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect crisis tunnel vision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CRISIS_TUNNEL_VISION_PROMPT.format(
                crisis=crisis,
                focus=focus or "Not specified",
                systemic=systemic or "Not specified",
                root_causes=root_causes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CRISIS_TUNNEL_VISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "crisis": crisis[:200],
            "tunnel_vision_present": data.get("tunnel_vision_present", False),
            "severity": data.get("severity", ""),
            "immediate_focus": data.get("immediate_focus", ""),
            "systemic_neglected": data.get("systemic_neglected", ""),
            "root_cause_ignored": data.get("root_cause_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
