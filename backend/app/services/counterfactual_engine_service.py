"""CounterfactualEngineService — Knowledge Dependency & What-If Analysis.

Maps the dependency structure of research claims and simulates what happens
when foundational claims are removed or negated. Identifies load-bearing
claims, fragile knowledge structures, and cascading failure paths.

Think of it as "blast radius analysis" for knowledge — if this one claim
turns out to be wrong, what else falls apart?
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEPENDENCY_MAP_SYSTEM = """You are a knowledge dependency analyst. Given research claims, map their logical dependency structure. A claim X depends on claim Y if negating Y would weaken or invalidate X.

Output JSON with structure: dependency_graph.claims (list of id/text/type/load_bearing_score), dependency_graph.edges (list of from/to/type/strength/explanation), dependency_graph.roots (foundational claim ids), dependency_graph.leaves (terminal claim ids), dependency_graph.critical_path (most important chain)."""

DEPENDENCY_MAP_PROMPT = """Research question: {question}

Claims to analyze:
{claims_text}

Map the logical dependency structure between these claims. Which claims depend on which others being true? Return ONLY valid JSON."""

COUNTERFACTUAL_SYSTEM = """You are a counterfactual reasoning expert. A claim has been NEGATED (assumed false). Trace cascading effects: what's invalidated, weakened, or unaffected.

Only mark "invalidated" if it logically requires the negated claim. "Weakened" if partially supported. "Unaffected" if independent.

Output JSON with: counterfactual.negated_claim, counterfactual.blast_radius (invalidated/weakened/unaffected/surprisingly_strengthened lists), counterfactual.cascade_depth, counterfactual.total_affected, counterfactual.severity (catastrophic|major|moderate|minor|negligible), counterfactual.recovery_paths, counterfactual.alternative_worlds."""

COUNTERFACTUAL_PROMPT = """Research question: {question}

Claim being NEGATED (assume this is FALSE):
"{negated_claim}"

Other claims in the knowledge structure:
{other_claims_text}

Known dependencies:
{dependencies_text}

Trace the cascading effects of this claim being false. Return ONLY valid JSON."""

FRAGILITY_SYSTEM = """You are a knowledge structure analyst. Assess overall fragility of a research knowledge base - how robust is it to individual claims being wrong?

Output JSON with: fragility_analysis.overall_robustness (0-1), fragility_analysis.single_points_of_failure (list of claim/blast_radius/risk_level), fragility_analysis.redundancy_score (0-1), fragility_analysis.weakest_link (claim/why), fragility_analysis.recommendations (list of action/priority/rationale), fragility_analysis.resilience_verdict (antifragile|robust|adequate|fragile|house_of_cards)."""

FRAGILITY_PROMPT = """Research question: {question}

Knowledge structure:
{structure_text}

Dependency graph summary:
- {num_claims} claims total
- {num_foundational} foundational (root) claims
- {num_derived} derived claims
- {max_depth} maximum dependency depth
- {num_edges} dependency edges

Counterfactual results for key claims:
{counterfactual_summary}

Assess the overall fragility of this knowledge structure. Return ONLY valid JSON."""

WHAT_IF_SYSTEM = """You are a scenario planning expert for research. Given a what-if scenario, trace implications: what changes, what opportunities open, what becomes impossible.

Output JSON with: scenario.premise, scenario.plausibility (0-1), scenario.implications (list of domain/effect/magnitude/timeline), scenario.opportunities_created, scenario.doors_closed, scenario.research_pivots_needed, scenario.early_signals, scenario.preparation_actions."""

WHAT_IF_PROMPT = """Research domain: {domain}

What-if scenario:
"{scenario}"

Current state of knowledge:
{knowledge_text}

Trace the full implications of this scenario. Return ONLY valid JSON."""


class CounterfactualEngineService:
    """Knowledge dependency mapping and what-if analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_dependencies(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
        claims: list[str] | None = None,
    ) -> dict:
        """Map the logical dependency structure between claims."""
        from app.clients.llm_client import LLMClient

        claim_list = claims or await self._gather_claims(question, dossier_id)
        if not claim_list:
            return {"error": "No claims found to analyze"}

        claims_text = "\n".join(
            f"{i+1}. {c[:150]}" for i, c in enumerate(claim_list[:15])
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEPENDENCY_MAP_PROMPT.format(
                question=question,
                claims_text=claims_text,
            ),
            system=DEPENDENCY_MAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        graph = data.get("dependency_graph", data)

        nodes = graph.get("claims", [])
        edges = graph.get("edges", [])
        roots = graph.get("roots", [])

        return {
            "question": question,
            "num_claims": len(nodes),
            "num_edges": len(edges),
            "num_foundational": len(roots),
            "claims": nodes,
            "edges": edges,
            "roots": roots,
            "leaves": graph.get("leaves", []),
            "critical_path": graph.get("critical_path", []),
        }

    async def negate_claim(
        self,
        question: str,
        claim_to_negate: str,
        *,
        dossier_id: str | None = None,
        other_claims: list[str] | None = None,
    ) -> dict:
        """Simulate negating a claim and trace cascading effects."""
        from app.clients.llm_client import LLMClient

        all_claims = other_claims or await self._gather_claims(question, dossier_id)
        remaining = [c for c in all_claims if c.strip() != claim_to_negate.strip()][:12]

        other_claims_text = "\n".join(
            f"- {c[:150]}" for c in remaining
        ) or "No other claims available"

        dep_result = await self.map_dependencies(
            question, claims=[claim_to_negate] + remaining
        )
        edges = dep_result.get("edges", [])
        dependencies_text = "\n".join(
            f"- {e.get('from','')} -> {e.get('to','')}: {e.get('type','')} ({e.get('explanation','')[:60]})"
            for e in edges[:15]
        ) or "Dependencies not mapped"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COUNTERFACTUAL_PROMPT.format(
                question=question,
                negated_claim=claim_to_negate[:200],
                other_claims_text=other_claims_text,
                dependencies_text=dependencies_text,
            ),
            system=COUNTERFACTUAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        cf = data.get("counterfactual", data)
        blast = cf.get("blast_radius", {})

        return {
            "negated_claim": claim_to_negate,
            "severity": cf.get("severity", "unknown"),
            "cascade_depth": cf.get("cascade_depth", 0),
            "total_affected": cf.get("total_affected", 0),
            "invalidated": blast.get("invalidated", []),
            "weakened": blast.get("weakened", []),
            "unaffected": blast.get("unaffected", []),
            "surprisingly_strengthened": blast.get("surprisingly_strengthened", []),
            "recovery_paths": cf.get("recovery_paths", []),
            "alternative_worlds": cf.get("alternative_worlds", []),
        }

    async def assess_fragility(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Assess overall fragility of the knowledge structure."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_claims(question, dossier_id)
        if not claims:
            return {"error": "No claims to assess"}

        dep_result = await self.map_dependencies(question, claims=claims)
        nodes = dep_result.get("claims", [])
        edges = dep_result.get("edges", [])
        roots = dep_result.get("roots", [])

        foundational = [n for n in nodes if n.get("type") == "foundational"]
        load_bearing = sorted(nodes, key=lambda n: n.get("load_bearing_score", 0), reverse=True)

        cf_summaries = []
        for lb in load_bearing[:3]:
            cf = await self.negate_claim(
                question, lb.get("text", ""), other_claims=claims
            )
            cf_summaries.append(
                f"If '{lb.get('text','')[:60]}' is false: "
                f"severity={cf.get('severity','?')}, "
                f"affected={cf.get('total_affected',0)}, "
                f"invalidated={len(cf.get('invalidated',[]))}"
            )

        max_depth = 0
        for node in nodes:
            depth = self._calc_depth(node.get("id", ""), edges)
            max_depth = max(max_depth, depth)

        structure_text = "\n".join(
            f"- [{n.get('type','?')}] (load={n.get('load_bearing_score',0):.1f}) {n.get('text','')[:80]}"
            for n in nodes[:12]
        )
        counterfactual_summary = "\n".join(f"- {s}" for s in cf_summaries) or "Not computed"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FRAGILITY_PROMPT.format(
                question=question,
                structure_text=structure_text,
                num_claims=len(nodes),
                num_foundational=len(foundational),
                num_derived=len(nodes) - len(foundational),
                max_depth=max_depth,
                num_edges=len(edges),
                counterfactual_summary=counterfactual_summary,
            ),
            system=FRAGILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        analysis = data.get("fragility_analysis", data)

        return {
            "question": question,
            "overall_robustness": analysis.get("overall_robustness", 0),
            "resilience_verdict": analysis.get("resilience_verdict", "unknown"),
            "single_points_of_failure": analysis.get("single_points_of_failure", []),
            "redundancy_score": analysis.get("redundancy_score", 0),
            "weakest_link": analysis.get("weakest_link", {}),
            "recommendations": analysis.get("recommendations", []),
            "diversification": analysis.get("diversification", {}),
        }

    async def what_if(
        self,
        scenario: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Explore a what-if scenario and trace its implications."""
        from app.clients.llm_client import LLMClient

        knowledge = await self._gather_knowledge(scenario, dossier_id)
        knowledge_text = "\n".join(
            f"- {k[:120]}" for k in knowledge[:10]
        ) or "General domain knowledge"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WHAT_IF_PROMPT.format(
                domain=domain or "research",
                scenario=scenario,
                knowledge_text=knowledge_text,
            ),
            system=WHAT_IF_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        sc = data.get("scenario", data)

        return {
            "scenario": scenario,
            "plausibility": sc.get("plausibility", 0),
            "implications": sc.get("implications", []),
            "opportunities_created": sc.get("opportunities_created", []),
            "doors_closed": sc.get("doors_closed", []),
            "research_pivots_needed": sc.get("research_pivots_needed", []),
            "early_signals": sc.get("early_signals", []),
            "preparation_actions": sc.get("preparation_actions", []),
        }

    # --- Private helpers ---

    def _calc_depth(self, node_id: str, edges: list[dict], visited: set | None = None) -> int:
        if visited is None:
            visited = set()
        if node_id in visited:
            return 0
        visited.add(node_id)
        parents = [e["from"] for e in edges if e.get("to") == node_id]
        if not parents:
            return 0
        return 1 + max(self._calc_depth(p, edges, visited) for p in parents)

    async def _gather_claims(self, question: str, dossier_id: str | None) -> list[str]:
        claims = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier and dossier.claims:
                    for c in dossier.claims[:15]:
                        if isinstance(c, dict):
                            claims.append(c.get("text", c.get("claim", str(c)))[:200])
                        else:
                            claims.append(str(c)[:200])
            except Exception:
                pass

        if not claims:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=question[:150], top_k=10)
                for r in results:
                    p = r.get("payload", {})
                    text = p.get("text", p.get("title", ""))[:200]
                    if text:
                        claims.append(text)
            except Exception:
                pass
        return claims

    async def _gather_knowledge(self, query: str, dossier_id: str | None) -> list[str]:
        knowledge = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:150], top_k=8)
            for r in results:
                p = r.get("payload", {})
                knowledge.append(p.get("text", p.get("title", ""))[:150])
        except Exception:
            pass
        return knowledge
