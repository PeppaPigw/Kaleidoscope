"""PreMortemService — Prospective Failure Analysis.

Instead of a post-mortem after failure, this imagines the project
has already failed and works backward to identify why. Leverages
prospective hindsight to overcome optimism bias and identify risks
that are hard to see from the inside.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRE_MORTEM_SYSTEM = """You are a pre-mortem facilitator. Given a plan or project, imagine it has ALREADY FAILED spectacularly. Work backward to explain why:
- What went wrong? (Assume failure is certain and explain it)
- What risks were ignored because of optimism bias?
- What single points of failure existed?
- What assumptions turned out to be wrong?
- What early warning signs were missed?

Output JSON with: failure_narrative (a plausible story of how it failed), root_causes (list of: cause, category (technical/human/market/timing/resource/political), likelihood (0-1), preventability (easy/moderate/hard/impossible)), ignored_risks (list of risks that optimism bias hid), single_points_of_failure (list of: point, what_happens_if_it_fails), wrong_assumptions (list of: assumption, why_it_seemed_safe, how_it_broke), early_warning_signs (list of: signal, when_visible, why_likely_ignored), most_likely_failure_mode (the single most probable way this fails), most_catastrophic_failure_mode (the worst-case scenario), prevention_actions (list of: action, which_failure_it_prevents, cost, priority (critical/high/medium/low)), kill_criteria (conditions that should trigger project cancellation), confidence_in_success (0-1, honest probability of success after this analysis)."""

PRE_MORTEM_PROMPT = """Conduct a pre-mortem:

Project/Plan: {plan}
Timeline: {timeline}
Team/Resources: {resources}
Success criteria: {success_criteria}
Domain: {domain}
Context: {context}

Imagine this has ALREADY FAILED. Why did it fail? Return ONLY valid JSON."""


class PreMortemService:
    """Conducts prospective failure analysis via pre-mortem."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        plan: str,
        *,
        timeline: str = "",
        resources: str = "",
        success_criteria: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Conduct pre-mortem analysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRE_MORTEM_PROMPT.format(
                plan=plan,
                timeline=timeline or "Not specified",
                resources=resources or "Not specified",
                success_criteria=success_criteria or "Not explicitly defined",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRE_MORTEM_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        return {
            "plan": plan[:200],
            "failure_narrative": data.get("failure_narrative", ""),
            "root_causes": data.get("root_causes", []),
            "ignored_risks": data.get("ignored_risks", []),
            "single_points_of_failure": data.get("single_points_of_failure", []),
            "wrong_assumptions": data.get("wrong_assumptions", []),
            "early_warning_signs": data.get("early_warning_signs", []),
            "most_likely_failure_mode": data.get("most_likely_failure_mode", ""),
            "most_catastrophic_failure_mode": data.get("most_catastrophic_failure_mode", ""),
            "prevention_actions": data.get("prevention_actions", []),
            "kill_criteria": data.get("kill_criteria", []),
            "confidence_in_success": data.get("confidence_in_success", 0),
        }
