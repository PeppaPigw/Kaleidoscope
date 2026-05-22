"""EpistemicLabyrinthService — Epistemic Labyrinth Detection.

Detects epistemic labyrinths — complex reasoning structures designed
to confuse and prevent finding the way out.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LABYRINTH_SYSTEM = """You are an epistemic labyrinth specialist. Given a reasoning structure, assess whether complexity is designed to confuse and prevent escape:

Key concepts:
- Epistemic labyrinth: complex structure designed to confuse
- Deliberate complexity: complexity serving confusion not clarity
- Exit prevention: structure preventing finding way out
- False paths: paths that appear to lead out but don't
- Disorientation design: designed to disorient
- Complexity as weapon: complexity used to trap
- Navigation impossibility: impossible to navigate to resolution

When epistemic labyrinth IS present:
- Complex reasoning structure designed to confuse
- Complexity serving confusion not clarity
- Structure preventing finding resolution
- Paths appearing to lead out but circling back
- Designed to disorient those navigating it
- Complexity used as weapon to trap
- Impossible to navigate to clear resolution

When productive complexity is present:
- Complexity reflecting genuine subject matter
- Complexity serving understanding not confusion
- Clear paths to resolution available
- Navigation possible with effort
- Complexity not designed to trap
- Complexity as feature not weapon
- Resolution achievable through careful navigation

Output JSON with: labyrinth_present (bool), severity (none/mild/moderate/severe), structure (what structure exists), complexity (what complexity is present), false_paths (what false paths exist), exit (whether exit is possible), recommendation (productive_complexity/mild_confusion/significant_labyrinth/major_deliberate_trap/simplify_and_find_exit)."""

EPISTEMIC_LABYRINTH_PROMPT = """Detect epistemic labyrinth:

Structure: {structure}
Complexity: {complexity}
False paths: {false_paths}
Exit: {exit_possibility}
Domain: {domain}
Context: {context}

Is complex reasoning designed to confuse and prevent finding the way out? Return ONLY valid JSON."""


class EpistemicLabyrinthService:
    """Detects epistemic labyrinths — complex structures designed to confuse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        complexity: str = "",
        false_paths: str = "",
        exit_possibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic labyrinth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LABYRINTH_PROMPT.format(
                structure=structure,
                complexity=complexity or "Not specified",
                false_paths=false_paths or "Not specified",
                exit_possibility=exit_possibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LABYRINTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "labyrinth_present": data.get("labyrinth_present", False),
            "severity": data.get("severity", ""),
            "complexity": data.get("complexity", ""),
            "false_paths": data.get("false_paths", ""),
            "exit": data.get("exit", ""),
            "recommendation": data.get("recommendation", ""),
        }
