"""WickedProblemService — Wicked Problem Assessment.

Identifies when a problem is "wicked" (Rittel & Webber 1973) —
no definitive formulation, no stopping rule, solutions are not
true/false but better/worse, every attempt changes the problem,
and stakeholders disagree on what the problem even is. Wicked
problems require different approaches than tame ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WICKED_SYSTEM = """You are a wicked problem specialist. Given a problem, assess whether it is "wicked" in the Rittel & Webber sense:
1. No definitive formulation — the problem definition depends on your perspective
2. No stopping rule — you can always do more, there's no "solved"
3. Solutions are not true/false but better/worse
4. No immediate or ultimate test — effects play out over time
5. Every solution is a "one-shot operation" — you can't experiment without consequences
6. No enumerable set of solutions
7. Every wicked problem is essentially unique
8. Every wicked problem is a symptom of another problem
9. Discrepancies can be explained in numerous ways
10. The planner has no right to be wrong — consequences are real

Output JSON with: wicked_problem (bool), wickedness_score (0-1), criteria_met (list of which Rittel-Webber criteria apply), problem_formulation_contested (bool — do stakeholders disagree on what the problem is?), stopping_rule_exists (bool — is there a clear "done"?), solution_testable (bool — can solutions be tested before full implementation?), stakeholder_disagreement (what stakeholders disagree about), problem_shifts_with_solution (bool — does attempting to solve it change the problem?), interconnected_problems (other problems this is entangled with), unique_aspects (what makes this unlike previous problems), irreversibility_of_attempts (how hard it is to undo solution attempts), value_conflicts (what values are in tension), appropriate_approach (what methodology suits wicked problems: design_thinking/adaptive_management/stakeholder_dialogue/satisficing/incremental), inappropriate_approach (what approaches will fail: optimization/engineering/top_down_planning), recommendation (treat_as_tame/acknowledge_wickedness/adaptive_approach/reframe_problem/decompose_carefully)."""

WICKED_PROMPT = """Assess problem wickedness:

Problem: {problem}
Stakeholders: {stakeholders}
Previous attempts: {previous_attempts}
Disagreements: {disagreements}
Domain: {domain}
Context: {context}

Is this a wicked problem? Return ONLY valid JSON."""


class WickedProblemService:
    """Assesses whether a problem is wicked in the Rittel-Webber sense."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        problem: str,
        *,
        stakeholders: str = "",
        previous_attempts: str = "",
        disagreements: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess problem wickedness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WICKED_PROMPT.format(
                problem=problem,
                stakeholders=stakeholders or "Not specified",
                previous_attempts=previous_attempts or "None noted",
                disagreements=disagreements or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WICKED_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "wicked_problem": data.get("wicked_problem", False),
            "wickedness_score": data.get("wickedness_score", 0),
            "criteria_met": data.get("criteria_met", []),
            "problem_formulation_contested": data.get("problem_formulation_contested", False),
            "stopping_rule_exists": data.get("stopping_rule_exists", False),
            "solution_testable": data.get("solution_testable", False),
            "stakeholder_disagreement": data.get("stakeholder_disagreement", ""),
            "problem_shifts_with_solution": data.get("problem_shifts_with_solution", False),
            "interconnected_problems": data.get("interconnected_problems", []),
            "unique_aspects": data.get("unique_aspects", ""),
            "irreversibility_of_attempts": data.get("irreversibility_of_attempts", ""),
            "value_conflicts": data.get("value_conflicts", ""),
            "appropriate_approach": data.get("appropriate_approach", ""),
            "inappropriate_approach": data.get("inappropriate_approach", ""),
            "recommendation": data.get("recommendation", ""),
        }
