"""SerendipityEngineService — Deliberate Discovery of Unexpected Connections.

The opposite of targeted search. Deliberately finds surprising juxtapositions,
unexpected connections, and "happy accidents" by combining distant concepts.
Many breakthroughs come from serendipitous connections between unrelated fields.

This engine manufactures serendipity by:
1. Bisociating distant concepts (Koestler's theory of creativity)
2. Random walks through knowledge space
3. Forced connections between unrelated domains
4. Anomaly-seeking in familiar territory
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BISOCIATE_SYSTEM = """You are a creative research catalyst specializing in bisociation - finding hidden connections between seemingly unrelated concepts. Arthur Koestler showed that creativity comes from connecting two habitually incompatible frames of reference.

Given two distant concepts, find the deepest non-obvious connection. Not surface similarity, but structural or functional parallels that could generate genuine insight.

Output JSON with: bisociation.concept_a, bisociation.concept_b, bisociation.connection (the hidden link), bisociation.depth (surface|structural|generative), bisociation.insight (what this connection reveals), bisociation.research_implications (list of what to investigate), bisociation.novelty (0-1), bisociation.testable_prediction (what this predicts), bisociation.surprise_factor (0-1)."""

BISOCIATE_PROMPT = """Concept A: {concept_a}
Domain A: {domain_a}

Concept B: {concept_b}
Domain B: {domain_b}

Context: {context}

Find the deepest non-obvious connection. Return ONLY valid JSON."""

RANDOM_WALK_SYSTEM = """You are a knowledge space explorer performing a random walk through conceptual territory. Starting from a seed concept, take unexpected jumps to distant but connected ideas. Each jump should be surprising but defensible.

Output JSON with: walk.seed, walk.steps (list of concept/domain/connection_to_previous/surprise_factor/potential_insight), walk.destination (where we ended up), walk.serendipitous_finding (the most unexpected discovery from the walk), walk.research_opportunity (what to investigate based on this walk)."""

RANDOM_WALK_PROMPT = """Seed concept: {seed}
Domain: {domain}
Number of jumps: {num_jumps}
Bias direction: {bias} (or 'none' for pure random)

Current research context:
{context_text}

Take {num_jumps} surprising conceptual jumps. Each should be unexpected but defensible. Return ONLY valid JSON."""

FORCED_CONNECTION_SYSTEM = """You are a forced-connection creativity expert. Given a research problem and a randomly selected distant concept, FORCE a meaningful connection. The constraint of forced connection often produces the most creative insights.

Even if the connection seems absurd at first, find the structural parallel. The best forced connections reveal something genuinely useful about the original problem.

Output JSON with: forced_connection.problem, forced_connection.random_concept, forced_connection.connection_found (the forced link), forced_connection.quality (absurd|tenuous|interesting|illuminating|breakthrough), forced_connection.mechanism (how the connection works), forced_connection.actionable_insight (what to do with this), forced_connection.new_hypothesis (a testable hypothesis from this connection), forced_connection.confidence (0-1)."""

FORCED_CONNECTION_PROMPT = """Research problem: {problem}
Domain: {domain}

Random concept to force-connect: {random_concept}
(from domain: {random_domain})

Force a meaningful connection. Even if it seems absurd, find the structural parallel. Return ONLY valid JSON."""

ANOMALY_SYSTEM = """You are an anomaly detector for research. Given a body of knowledge, find what DOESN'T fit - the unexplained observations, the contradictions everyone ignores, the elephants in the room. Anomalies are where breakthroughs hide.

Output JSON with: anomalies (list of observation/expected_behavior/actual_behavior/severity/ignored_because/potential_explanation/research_value 0-1), most_promising_anomaly (the one most likely to lead to a breakthrough), meta_pattern (what the anomalies collectively suggest)."""

ANOMALY_PROMPT = """Research domain: {domain}
Current understanding: {understanding_text}
Known claims: {claims_text}

Find the anomalies - what doesn't fit, what's unexplained, what everyone ignores. Return ONLY valid JSON."""


class SerendipityEngineService:
    """Deliberate discovery of unexpected connections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def bisociate(
        self,
        concept_a: str,
        concept_b: str,
        *,
        domain_a: str = "",
        domain_b: str = "",
        context: str = "",
    ) -> dict:
        """Find hidden connections between two distant concepts."""
        from app.clients.llm_client import LLMClient

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BISOCIATE_PROMPT.format(
                concept_a=concept_a,
                concept_b=concept_b,
                domain_a=domain_a or "unspecified",
                domain_b=domain_b or "unspecified",
                context=context or "General research",
            ),
            system=BISOCIATE_SYSTEM,
            max_tokens=4096,
            temperature=0.6,
        )
        data = parse_llm_json(raw)
        b = data.get("bisociation", data)

        return {
            "concept_a": concept_a,
            "concept_b": concept_b,
            "connection": b.get("connection", ""),
            "depth": b.get("depth", "surface"),
            "insight": b.get("insight", ""),
            "research_implications": b.get("research_implications", []),
            "novelty": b.get("novelty", 0),
            "testable_prediction": b.get("testable_prediction", ""),
            "surprise_factor": b.get("surprise_factor", 0),
        }

    async def random_walk(
        self,
        seed: str,
        *,
        domain: str = "",
        num_jumps: int = 5,
        bias: str = "none",
        dossier_id: str | None = None,
    ) -> dict:
        """Take a random walk through knowledge space from a seed concept."""
        from app.clients.llm_client import LLMClient

        context = await self._gather_context(seed, dossier_id)
        context_text = "\n".join(f"- {c}" for c in context[:6]) or "No specific context"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RANDOM_WALK_PROMPT.format(
                seed=seed,
                domain=domain or "any",
                num_jumps=min(num_jumps, 7),
                bias=bias or "none",
                context_text=context_text,
            ),
            system=RANDOM_WALK_SYSTEM,
            max_tokens=4096,
            temperature=0.7,
        )
        data = parse_llm_json(raw)
        walk = data.get("walk", data)

        steps = walk.get("steps", [])
        avg_surprise = 0.0
        if steps:
            try:
                avg_surprise = sum(float(s.get("surprise_factor", 0)) for s in steps) / len(steps)
            except (TypeError, ValueError):
                avg_surprise = 0.5

        return {
            "seed": seed,
            "steps": steps,
            "num_jumps": len(steps),
            "destination": walk.get("destination", ""),
            "serendipitous_finding": walk.get("serendipitous_finding", ""),
            "research_opportunity": walk.get("research_opportunity", ""),
            "average_surprise": round(avg_surprise, 2),
        }

    async def force_connection(
        self,
        problem: str,
        *,
        domain: str = "",
        random_concept: str = "",
        random_domain: str = "",
    ) -> dict:
        """Force a connection between a research problem and a random concept."""
        from app.clients.llm_client import LLMClient
        import random

        if not random_concept:
            distant_concepts = [
                ("mycorrhizal networks", "ecology"),
                ("jazz improvisation", "music theory"),
                ("tidal patterns", "oceanography"),
                ("origami folding", "mathematics"),
                ("ant colony optimization", "entomology"),
                ("fermentation", "biochemistry"),
                ("plate tectonics", "geology"),
                ("immune system memory", "immunology"),
                ("market microstructure", "finance"),
                ("dream consolidation", "neuroscience"),
                ("crystal growth", "materials science"),
                ("predator-prey dynamics", "ecology"),
                ("language creolization", "linguistics"),
                ("volcanic eruption prediction", "volcanology"),
                ("sourdough starter", "microbiology"),
            ]
            random_concept, random_domain = random.choice(distant_concepts)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FORCED_CONNECTION_PROMPT.format(
                problem=problem,
                domain=domain or "research",
                random_concept=random_concept,
                random_domain=random_domain or "unspecified",
            ),
            system=FORCED_CONNECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.6,
        )
        data = parse_llm_json(raw)
        fc = data.get("forced_connection", data)

        return {
            "problem": problem,
            "random_concept": random_concept,
            "random_domain": random_domain,
            "connection_found": fc.get("connection_found", ""),
            "quality": fc.get("quality", "tenuous"),
            "mechanism": fc.get("mechanism", ""),
            "actionable_insight": fc.get("actionable_insight", ""),
            "new_hypothesis": fc.get("new_hypothesis", ""),
            "confidence": fc.get("confidence", 0),
        }

    async def find_anomalies(
        self,
        domain: str,
        *,
        dossier_id: str | None = None,
        understanding: str = "",
    ) -> dict:
        """Find anomalies and unexplained observations in a research domain."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_context(domain, dossier_id)
        claims_text = "\n".join(f"- {c}" for c in claims[:10]) or "General domain knowledge"
        understanding_text = understanding or "Standard understanding in the field"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANOMALY_PROMPT.format(
                domain=domain,
                understanding_text=understanding_text[:300],
                claims_text=claims_text,
            ),
            system=ANOMALY_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        anomalies = data.get("anomalies", [])
        high_value = [a for a in anomalies if a.get("research_value", 0) > 0.7]

        return {
            "domain": domain,
            "anomalies_found": len(anomalies),
            "high_value_anomalies": len(high_value),
            "anomalies": anomalies,
            "most_promising": data.get("most_promising_anomaly", ""),
            "meta_pattern": data.get("meta_pattern", ""),
        }

    # --- Private helpers ---

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        context = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:150], top_k=6)
            for r in results:
                p = r.get("payload", {})
                context.append(p.get("text", p.get("title", ""))[:120])
        except Exception:
            pass
        return context
