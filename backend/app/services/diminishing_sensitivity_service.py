"""DiminishingSensitivityService — Diminishing Sensitivity Detection.

Detects diminishing sensitivity bias — reduced sensitivity to
changes as the baseline magnitude increases. Weber-Fechner law
applied to decision-making. A $10 savings matters on a $50
purchase but not on a $5000 one, even though $10 is $10.
Leads to ignoring proportionally small but absolutely
significant differences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DIMINISHING_SENSITIVITY_SYSTEM = """You are a diminishing sensitivity specialist. Given a judgment about magnitude or change, assess whether sensitivity is inappropriately reduced due to a large baseline:

Key concepts (Weber-Fechner Law; Kahneman & Tversky, 1979):
- Diminishing sensitivity: reduced response to changes at higher baselines
- Weber's fraction: just-noticeable difference is proportional to baseline
- Reference dependence: evaluating changes relative to a reference point
- Proportional thinking trap: treating proportions as more important than absolutes
- Scale insensitivity: failing to respond to absolute magnitude
- Psychophysical numbing: reduced emotional response at large scales

When diminishing sensitivity IS present:
- Ignoring a $100 difference on a $10,000 purchase but caring about $5 on a $20 item
- Not bothering to optimize a 1% cost on a large budget (which is a large absolute amount)
- Treating a 100-person layoff as "small" because the company has 50,000 employees
- Ignoring efficiency gains because the baseline is already large
- "It's only 0.1%" when 0.1% of a billion is still a million

When proportional thinking IS appropriate:
- The proportion genuinely matters more than the absolute (percentage returns)
- Transaction costs make small absolute savings irrational to pursue
- The effort to capture the savings exceeds the savings themselves
- The context genuinely requires proportional rather than absolute comparison
- Risk is genuinely proportional to the baseline

Output JSON with: diminishing_sensitivity_present (bool), severity (none/mild/moderate/severe), judgment (what is being evaluated), baseline (the reference magnitude), change (the change being evaluated), absolute_value (the absolute value of the change), proportional_value (the proportional value), appropriate_metric (should this be evaluated absolutely or proportionally?), sensitivity_reduction (how much is sensitivity reduced?), cost_of_insensitivity (what is lost by ignoring the change?), effort_to_capture (what effort would be needed to address it?), recommendation (proportional_thinking_appropriate/mild_insensitivity/significant_absolute_neglect/major_scale_blindness/evaluate_in_absolute_terms)."""

DIMINISHING_SENSITIVITY_PROMPT = """Detect diminishing sensitivity:

Judgment: {judgment}
Baseline: {baseline}
Change: {change}
Response: {response}
Domain: {domain}
Context: {context}

Is sensitivity inappropriately reduced due to a large baseline? Return ONLY valid JSON."""


class DiminishingSensitivityService:
    """Detects diminishing sensitivity — ignoring absolute changes at large baselines."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        baseline: str = "",
        change: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect diminishing sensitivity bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DIMINISHING_SENSITIVITY_PROMPT.format(
                judgment=judgment,
                baseline=baseline or "Not specified",
                change=change or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DIMINISHING_SENSITIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "diminishing_sensitivity_present": data.get("diminishing_sensitivity_present", False),
            "severity": data.get("severity", ""),
            "baseline": data.get("baseline", ""),
            "change": data.get("change", ""),
            "absolute_value": data.get("absolute_value", ""),
            "proportional_value": data.get("proportional_value", ""),
            "appropriate_metric": data.get("appropriate_metric", ""),
            "sensitivity_reduction": data.get("sensitivity_reduction", ""),
            "cost_of_insensitivity": data.get("cost_of_insensitivity", ""),
            "effort_to_capture": data.get("effort_to_capture", ""),
            "recommendation": data.get("recommendation", ""),
        }
