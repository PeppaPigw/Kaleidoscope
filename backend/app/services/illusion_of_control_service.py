"""IllusionOfControlService — Illusion of Control Detection.

Detects illusion of control — overestimating one's ability to
influence outcomes that are largely determined by chance or
external factors. Langer (1975). Blowing on dice, choosing
lottery numbers, superstitious rituals. Leads to excessive
risk-taking and failure to prepare for uncontrollable outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ILLUSION_CONTROL_SYSTEM = """You are an illusion of control specialist. Given a situation where someone believes they can influence an outcome, assess whether that belief is justified or illusory:

Key concepts (Langer, 1975):
- Illusion of control: overestimating personal influence over chance events
- Skill-chance confusion: treating chance outcomes as if skill matters
- Choice illusion: feeling more control when you choose (lottery numbers)
- Familiarity effect: feeling more control over familiar random processes
- Active involvement: feeling more control when physically involved
- Competition framing: feeling more control against a "weaker" opponent in chance games
- Outcome sequence: past successes inflate perceived control

When illusion of control IS present:
- Believing personal actions influence random outcomes
- Superstitious behaviors treated as causal
- "I'm on a hot streak" in purely random processes
- Excessive confidence in ability to time markets, predict weather, etc.
- Rituals or habits believed to affect uncontrollable outcomes
- Refusing to delegate because "only I can make this work"

When the control IS real:
- The person's actions genuinely affect the outcome (skill-based)
- There is a documented causal mechanism
- The degree of claimed control matches empirical evidence
- Others with similar actions achieve similar outcomes
- The outcome has a genuine skill component (even if also luck)

Output JSON with: illusion_of_control_present (bool), severity (none/mild/moderate/severe), situation (what outcome is being influenced), claimed_control (what control is being claimed), actual_control (what control actually exists), skill_component (how much is genuinely skill-based?), chance_component (how much is genuinely chance?), evidence_of_influence (what evidence supports the claimed control?), base_rate_success (what is the base rate without the claimed control?), risk_of_illusion (what risks does the illusion create?), adaptive_value (does the illusion serve any useful purpose?), recommendation (control_justified/mild_overestimation/significant_illusion/major_control_fantasy/accept_uncertainty)."""

ILLUSION_CONTROL_PROMPT = """Detect illusion of control:

Situation: {situation}
Claimed influence: {influence}
Evidence of control: {evidence}
Outcome history: {history}
Domain: {domain}
Context: {context}

Is the person overestimating their control over this outcome? Return ONLY valid JSON."""


class IllusionOfControlService:
    """Detects illusion of control — overestimating influence over chance outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        influence: str = "",
        evidence: str = "",
        history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusion of control."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ILLUSION_CONTROL_PROMPT.format(
                situation=situation,
                influence=influence or "Not specified",
                evidence=evidence or "Not specified",
                history=history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ILLUSION_CONTROL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "illusion_of_control_present": data.get("illusion_of_control_present", False),
            "severity": data.get("severity", ""),
            "claimed_control": data.get("claimed_control", ""),
            "actual_control": data.get("actual_control", ""),
            "skill_component": data.get("skill_component", ""),
            "chance_component": data.get("chance_component", ""),
            "evidence_of_influence": data.get("evidence_of_influence", ""),
            "base_rate_success": data.get("base_rate_success", ""),
            "risk_of_illusion": data.get("risk_of_illusion", ""),
            "adaptive_value": data.get("adaptive_value", ""),
            "recommendation": data.get("recommendation", ""),
        }
