"""OmissionBiasService — Omission Bias Detection.

Detects omission bias — preferring harmful inaction over less
harmful action. Spranca, Minsk & Baron (1991). People judge
harmful actions as worse than equally harmful omissions.
"Letting die" feels less wrong than "killing" even when the
outcome is identical. Leads to inaction when action would
produce better outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OMISSION_SYSTEM = """You are an omission bias specialist. Given a decision between action and inaction, assess whether omission bias is causing preference for harmful inaction:

Key concepts (Spranca, Minsk & Baron, 1991):
- Omission bias: judging harmful actions as worse than equally harmful omissions
- Act/omission distinction: moral asymmetry between doing and allowing
- Status quo bias overlap: inaction preserves the status quo
- Trolley problem: active intervention feels worse than passive allowing
- Regret asymmetry: anticipated regret is greater for actions than omissions
- Naturalness preference: "natural" outcomes from inaction feel more acceptable

When omission bias IS present:
- Refusing to act when action would clearly produce better outcomes
- "At least I didn't cause it" when inaction caused equal or greater harm
- Preferring to "let things play out" when intervention would help
- Vaccine hesitancy: risk of action (side effects) weighted more than risk of inaction (disease)
- Regulatory inaction: not approving a beneficial drug because action requires justification
- "Do no harm" interpreted as "do nothing" rather than "minimize total harm"

When inaction IS appropriate:
- Genuine uncertainty about whether action will help or harm
- The action has irreversible consequences and more information is coming
- The system is self-correcting and intervention would interfere
- The action would violate autonomy or consent
- The costs of action genuinely exceed the costs of inaction

Output JSON with: omission_bias_present (bool), severity (none/mild/moderate/severe), situation (what decision is being faced), action_option (what could be done), inaction_option (what happens if nothing is done), action_harm (potential harm from acting), inaction_harm (potential harm from not acting), net_comparison (which option produces less total harm?), regret_asymmetry (bool — is anticipated regret driving the preference?), responsibility_avoidance (bool — is avoiding causal responsibility the motive?), naturalness_appeal (bool — is "natural outcome" being used to justify inaction?), reversibility (can the action be undone?), information_gap (is more information genuinely needed?), recommendation (inaction_justified/mild_omission_bias/significant_omission_bias/major_omission_bias/act_to_minimize_harm)."""

OMISSION_PROMPT = """Detect omission bias:

Situation: {situation}
Action available: {action}
Consequence of inaction: {inaction}
Reasoning for not acting: {reasoning}
Domain: {domain}
Context: {context}

Is omission bias causing preference for harmful inaction? Return ONLY valid JSON."""


class OmissionBiasService:
    """Detects omission bias — preferring harmful inaction over less harmful action."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        action: str = "",
        inaction: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect omission bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OMISSION_PROMPT.format(
                situation=situation,
                action=action or "Not specified",
                inaction=inaction or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OMISSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "omission_bias_present": data.get("omission_bias_present", False),
            "severity": data.get("severity", ""),
            "action_option": data.get("action_option", ""),
            "inaction_option": data.get("inaction_option", ""),
            "action_harm": data.get("action_harm", ""),
            "inaction_harm": data.get("inaction_harm", ""),
            "net_comparison": data.get("net_comparison", ""),
            "regret_asymmetry": data.get("regret_asymmetry", False),
            "responsibility_avoidance": data.get("responsibility_avoidance", False),
            "naturalness_appeal": data.get("naturalness_appeal", False),
            "reversibility": data.get("reversibility", ""),
            "information_gap": data.get("information_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
