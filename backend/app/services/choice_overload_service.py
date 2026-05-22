"""ChoiceOverloadService — Choice Overload Detection.

Detects choice overload — decision quality and satisfaction
decreasing as the number of options increases. Iyengar &
Lepper (2000). The jam study: 24 jams → fewer purchases than
6 jams. Too many options lead to decision paralysis, regret,
and suboptimal choices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHOICE_OVERLOAD_SYSTEM = """You are a choice overload specialist. Given a decision situation, assess whether too many options are degrading decision quality:

Key concepts (Iyengar & Lepper, 2000; Schwartz, 2004):
- Choice overload: too many options reduce decision quality and satisfaction
- Paradox of choice: more options → more regret, less satisfaction
- Decision fatigue: cognitive resources depleted by too many choices
- Maximizing vs. satisficing: maximizers suffer more from overload
- Option paralysis: inability to choose when options are too numerous
- Post-decision regret: more options → more counterfactual thinking
- Cognitive load: evaluating many options exceeds working memory

When choice overload IS present:
- Decision paralysis from too many options
- Defaulting to no choice rather than choosing among many
- Excessive time spent comparing marginal differences
- Post-decision regret driven by awareness of unchosen alternatives
- Choosing randomly or by irrelevant criteria due to overwhelm
- "I'll decide later" repeatedly due to option volume

When many options ARE manageable:
- Options are well-organized into categories
- Clear criteria exist for evaluation
- The person has expertise in the domain
- Options differ on few, clear dimensions
- Decision aids or filters reduce effective choice set
- The stakes are low enough that any choice is acceptable

Output JSON with: choice_overload_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), option_count (how many options), effective_differences (how many meaningfully different options exist), decision_criteria (what criteria are being used), cognitive_load (how demanding is the comparison?), paralysis_present (bool — is the person stuck?), regret_risk (how likely is post-decision regret?), simplification_possible (can options be reduced or categorized?), recommendation (options_manageable/mild_overload/significant_paralysis/major_choice_overload/reduce_option_set)."""

CHOICE_OVERLOAD_PROMPT = """Detect choice overload:

Decision: {decision}
Options: {options}
Criteria: {criteria}
Current state: {state}
Domain: {domain}
Context: {context}

Are too many options degrading decision quality? Return ONLY valid JSON."""


class ChoiceOverloadService:
    """Detects choice overload — too many options degrading decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        options: str = "",
        criteria: str = "",
        state: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect choice overload."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHOICE_OVERLOAD_PROMPT.format(
                decision=decision,
                options=options or "Not specified",
                criteria=criteria or "Not specified",
                state=state or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHOICE_OVERLOAD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "choice_overload_present": data.get("choice_overload_present", False),
            "severity": data.get("severity", ""),
            "option_count": data.get("option_count", ""),
            "effective_differences": data.get("effective_differences", ""),
            "decision_criteria": data.get("decision_criteria", ""),
            "cognitive_load": data.get("cognitive_load", ""),
            "paralysis_present": data.get("paralysis_present", False),
            "regret_risk": data.get("regret_risk", ""),
            "simplification_possible": data.get("simplification_possible", ""),
            "recommendation": data.get("recommendation", ""),
        }
