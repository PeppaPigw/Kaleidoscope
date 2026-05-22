"""BrooksLawService — Brooks' Law Detection.

Detects Brooks' Law — adding manpower to a late software project
makes it later. Fred Brooks (1975), The Mythical Man-Month.
New people need ramp-up time, communication overhead grows as
n(n-1)/2, and tasks may not be parallelizable. The mythical
man-month assumes people and months are interchangeable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BROOKS_SYSTEM = """You are a Brooks' Law specialist. Given a project staffing decision, assess whether Brooks' Law dynamics will make things worse:

Key concepts (Brooks, 1975 — The Mythical Man-Month):
- Brooks' Law: adding people to a late project makes it later
- Communication overhead: grows as n(n-1)/2 with team size
- Ramp-up time: new people are net negative before they're productive
- Task partitioning: not all work can be parallelized (9 women can't make a baby in 1 month)
- Mythical man-month: the false assumption that people and time are interchangeable
- Second-system effect: tendency to over-engineer the next version

When Brooks' Law WILL apply:
- Project is already late and adding people
- Tasks have high interdependency (can't be parallelized)
- Existing team must stop to onboard newcomers
- Communication paths will increase significantly
- Domain knowledge is deep and takes time to acquire
- The deadline is too close for ramp-up to pay off

When adding people CAN help:
- Tasks are genuinely independent and parallelizable
- New people have relevant domain expertise (minimal ramp-up)
- There's enough time for ramp-up before the deadline
- The work is well-documented and modular
- Communication overhead is managed (small teams, clear interfaces)

Output JSON with: brooks_law_applies (bool), severity (none/mild/moderate/severe), current_team_size (how many people now), proposed_addition (how many being added), project_lateness (how late the project is), ramp_up_time (how long new people need to be productive), communication_overhead_increase (how much coordination cost grows), task_parallelizability (can the remaining work be split?), deadline_proximity (how close is the deadline vs ramp-up time), existing_team_disruption (how much current team is slowed by onboarding), net_effect_timeline (will adding people actually help or hurt the timeline?), mythical_man_month_thinking (bool — treating people and time as interchangeable?), alternative_approaches (what else could be done instead of adding people), recommendation (addition_helpful/mild_brooks_effect/significant_brooks_law/adding_will_make_it_later/reduce_scope_instead)."""

BROOKS_PROMPT = """Detect Brooks' Law:

Situation: {situation}
Team/Staffing: {staffing}
Project status: {status}
Task structure: {tasks}
Domain: {domain}
Context: {context}

Will adding people make this late project later? Return ONLY valid JSON."""


class BrooksLawService:
    """Detects Brooks' Law — adding people to late projects makes them later."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        staffing: str = "",
        status: str = "",
        tasks: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Brooks' Law."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BROOKS_PROMPT.format(
                situation=situation,
                staffing=staffing or "Not specified",
                status=status or "Not specified",
                tasks=tasks or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BROOKS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "brooks_law_applies": data.get("brooks_law_applies", False),
            "severity": data.get("severity", ""),
            "current_team_size": data.get("current_team_size", ""),
            "proposed_addition": data.get("proposed_addition", ""),
            "project_lateness": data.get("project_lateness", ""),
            "ramp_up_time": data.get("ramp_up_time", ""),
            "communication_overhead_increase": data.get("communication_overhead_increase", ""),
            "task_parallelizability": data.get("task_parallelizability", ""),
            "deadline_proximity": data.get("deadline_proximity", ""),
            "existing_team_disruption": data.get("existing_team_disruption", ""),
            "net_effect_timeline": data.get("net_effect_timeline", ""),
            "mythical_man_month_thinking": data.get("mythical_man_month_thinking", False),
            "alternative_approaches": data.get("alternative_approaches", ""),
            "recommendation": data.get("recommendation", ""),
        }
