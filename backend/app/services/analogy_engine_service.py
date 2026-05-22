"""AnalogyEngineService — Cross-Domain Analogical Reasoning.

Finds structural similarities between problems in different domains and
transfers solutions across fields. Enables insights like "this NLP problem
is structurally identical to this solved problem in epidemiology."
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FIND_ANALOGIES_SYSTEM = """You are a cross-domain analogical reasoning expert. Given a problem or phenomenon, find structurally similar problems in DIFFERENT domains. The best analogies share deep structural properties, not surface features.

Focus on:
- Shared causal structure (same type of mechanism)
- Shared mathematical structure (same equations/dynamics)
- Shared constraint structure (same tradeoffs)
- Shared failure modes (breaks the same way)

Output JSON only:
{"analogies": [{"id": "ana_1", "source_domain": "the other field", "source_problem": "the analogous problem there", "structural_mapping": {"target_element": "source_element", "target_element2": "source_element2"}, "shared_structure": "what's structurally identical", "depth": "surface|structural|deep", "strength": 0.0-1.0, "known_solution_in_source": "how they solved it there", "transferable_insight": "what we can learn from the analogy", "limitations": ["where the analogy breaks down"], "novel": true}], "best_analogy": "the single most illuminating one", "meta_pattern": "the abstract pattern that connects all these analogies"}"""

FIND_ANALOGIES_PROMPT = """Problem/phenomenon to find analogies for:
{problem_text}

Domain: {domain}

Key properties:
{properties_text}

Constraints and tradeoffs:
{constraints_text}

Known approaches that have been tried:
{approaches_text}

Find deep structural analogies in OTHER domains. Prioritize analogies where the source domain has solved the problem. Return ONLY valid JSON."""

TRANSFER_SYSTEM = """You are a solution transfer specialist. Given a structural analogy between two domains, work out exactly how a solution from the source domain could be adapted to the target domain.

Output JSON only:
{"transfer_plan": {"source_solution": "what works in the source domain", "target_problem": "what we're trying to solve", "mapping": [{"source_concept": "concept there", "target_concept": "concept here", "adaptation_needed": "how to modify it"}], "transfer_steps": [{"step": 1, "action": "what to do", "rationale": "why this maps", "risk": "what could go wrong"}], "expected_benefit": "what we gain", "transfer_difficulty": "trivial|moderate|hard|speculative", "validation_method": "how to check if the transfer worked", "novel_predictions": ["what the analogy predicts that hasn't been tested"], "failure_modes": ["how the transfer could fail"]}}"""

TRANSFER_PROMPT = """Analogy to transfer:

Source domain: {source_domain}
Source problem: {source_problem}
Source solution: {source_solution}

Target domain: {target_domain}
Target problem: {target_problem}

Structural mapping:
{mapping_text}

Where the analogy breaks down:
{limitations_text}

Work out how to transfer the solution. Return ONLY valid JSON."""

ABSTRACT_SYSTEM = """You are a pattern abstraction expert. Given multiple specific instances of a phenomenon across different domains, extract the abstract pattern — the domain-independent principle that explains all instances.

Output JSON only:
{"abstraction": {"pattern_name": "short name for the pattern", "formal_description": "the abstract principle in domain-independent language", "mathematical_form": "equation or formal structure if applicable", "instances": [{"domain": "field", "manifestation": "how it appears there", "key_parameters": {"param": "value"}}], "predictions": [{"domain": "new field where this might apply", "predicted_manifestation": "what we'd expect to see", "testable": true}], "known_in_literature_as": "existing name if this pattern is already known (or 'novel')", "generative_power": 0.0-1.0, "explanatory_scope": "how many phenomena this explains"}}"""

ABSTRACT_PROMPT = """Instances to abstract from:

{instances_text}

Shared properties observed:
{shared_text}

Extract the abstract, domain-independent pattern. Return ONLY valid JSON."""


class AnalogyEngineService:
    """Cross-domain analogical reasoning and solution transfer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_analogies(
        self,
        problem: str,
        *,
        domain: str = "",
        properties: list[str] | None = None,
        constraints: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Find structural analogies in other domains."""
        from app.clients.llm_client import LLMClient

        approaches = await self._gather_approaches(problem, dossier_id)

        properties_text = "\n".join(
            f"- {p}" for p in (properties or [])
        ) or "Not explicitly characterized"

        constraints_text = "\n".join(
            f"- {c}" for c in (constraints or [])
        ) or "Not explicitly stated"

        approaches_text = "\n".join(
            f"- {a}" for a in approaches[:6]
        ) or "No known approaches"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FIND_ANALOGIES_PROMPT.format(
                problem_text=problem,
                domain=domain or "not specified",
                properties_text=properties_text,
                constraints_text=constraints_text,
                approaches_text=approaches_text,
            ),
            system=FIND_ANALOGIES_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        analogies = data.get("analogies", [])
        deep = [a for a in analogies if a.get("depth") == "deep"]
        with_solutions = [a for a in analogies if a.get("known_solution_in_source")]

        return {
            "problem": problem,
            "domain": domain,
            "analogies_found": len(analogies),
            "deep_analogies": len(deep),
            "with_transferable_solutions": len(with_solutions),
            "analogies": analogies,
            "best_analogy": data.get("best_analogy", ""),
            "meta_pattern": data.get("meta_pattern", ""),
        }

    async def transfer_solution(
        self,
        source_domain: str,
        source_problem: str,
        source_solution: str,
        target_domain: str,
        target_problem: str,
        *,
        structural_mapping: dict | None = None,
        limitations: list[str] | None = None,
    ) -> dict:
        """Transfer a solution from one domain to another via structural analogy."""
        from app.clients.llm_client import LLMClient

        mapping_text = "\n".join(
            f"- {k} → {v}" for k, v in (structural_mapping or {}).items()
        ) or "Mapping not explicitly provided — infer from context"

        limitations_text = "\n".join(
            f"- {l}" for l in (limitations or [])
        ) or "Limitations not characterized"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRANSFER_PROMPT.format(
                source_domain=source_domain,
                source_problem=source_problem,
                source_solution=source_solution,
                target_domain=target_domain,
                target_problem=target_problem,
                mapping_text=mapping_text,
                limitations_text=limitations_text,
            ),
            system=TRANSFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        plan = data.get("transfer_plan", data)

        return {
            "source": f"{source_domain}: {source_problem}",
            "target": f"{target_domain}: {target_problem}",
            "transfer_steps": plan.get("transfer_steps", []),
            "transfer_difficulty": plan.get("transfer_difficulty", "unknown"),
            "expected_benefit": plan.get("expected_benefit", ""),
            "novel_predictions": plan.get("novel_predictions", []),
            "validation_method": plan.get("validation_method", ""),
            "failure_modes": plan.get("failure_modes", []),
            "mapping": plan.get("mapping", []),
        }

    async def abstract_pattern(
        self,
        instances: list[dict],
    ) -> dict:
        """Extract an abstract pattern from multiple domain-specific instances."""
        from app.clients.llm_client import LLMClient

        instances_text = "\n\n".join(
            f"--- Instance {i+1} ---\n"
            f"Domain: {inst.get('domain', '?')}\n"
            f"Phenomenon: {inst.get('phenomenon', inst.get('problem', '?'))}\n"
            f"Key features: {inst.get('features', inst.get('properties', '?'))}"
            for i, inst in enumerate(instances[:6])
        ) or "No instances provided"

        shared_text = "Infer shared properties from the instances"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABSTRACT_PROMPT.format(
                instances_text=instances_text,
                shared_text=shared_text,
            ),
            system=ABSTRACT_SYSTEM,
            max_tokens=3072,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        abstraction = data.get("abstraction", data)

        return {
            "pattern_name": abstraction.get("pattern_name", ""),
            "formal_description": abstraction.get("formal_description", ""),
            "mathematical_form": abstraction.get("mathematical_form", ""),
            "instances": abstraction.get("instances", []),
            "predictions": abstraction.get("predictions", []),
            "known_as": abstraction.get("known_in_literature_as", "novel"),
            "generative_power": abstraction.get("generative_power", 0),
        }

    # --- Private helpers ---

    async def _gather_approaches(self, problem: str, dossier_id: str | None) -> list[str]:
        approaches = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{problem[:100]} approach method solution", top_k=5)
            for r in results:
                p = r.get("payload", {})
                approaches.append(p.get("title", p.get("text", ""))[:100])
        except Exception:
            pass
        return approaches
