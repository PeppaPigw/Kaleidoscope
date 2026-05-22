"""SynthesisEngineService — Cross-Dossier Synthesis & Emergent Hypothesis Generation.

Takes findings from multiple research threads (dossiers, claims, experiments,
verification results) and produces novel meta-insights: convergent evidence
patterns, contradictions, emergent hypotheses, and research frontier maps.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONVERGENCE_SYSTEM = """You are a research synthesis expert. Given claims and findings from multiple independent research threads, identify convergent evidence patterns — places where independent lines of inquiry point to the same conclusion from different angles.

Output JSON only:
{"convergence_map": {"patterns": [{"id": "conv_1", "thesis": "the convergent conclusion", "evidence_streams": [{"dossier_id": "id", "claim_text": "supporting claim", "confidence": 0.0-1.0, "methodology": "how this was established"}], "convergence_strength": 0.0-1.0, "independence_score": 0.0-1.0, "surprise_factor": 0.0-1.0, "implications": ["what this means"]}], "meta_confidence": 0.0-1.0, "strongest_signal": "one sentence"}}"""

CONVERGENCE_PROMPT = """Research threads to synthesize:

{threads_text}

Cross-cutting claims (from global ledger):
{claims_text}

Experimental results:
{experiments_text}

Identify convergent evidence patterns. Focus on conclusions supported by INDEPENDENT methodologies. Return ONLY valid JSON."""

CONTRADICTION_SYSTEM = """You are a research contradiction analyst. Given claims from multiple sources, identify genuine contradictions — not just different framings, but cases where findings are mutually incompatible.

Output JSON only:
{"contradictions": [{"id": "contra_1", "claim_a": {"text": "claim", "source": "dossier/paper", "confidence": 0.0-1.0, "methodology": "how established"}, "claim_b": {"text": "opposing claim", "source": "dossier/paper", "confidence": 0.0-1.0, "methodology": "how established"}, "contradiction_type": "direct|boundary|methodological|scope", "severity": "fundamental|significant|minor", "possible_resolutions": [{"hypothesis": "how both could be true", "testable": true, "test_description": "how to test"}], "research_priority": 0.0-1.0}], "highest_priority": "one sentence summary of most important contradiction"}"""

CONTRADICTION_PROMPT = """Claims from multiple research threads:

{claims_text}

Verification results (if any):
{verification_text}

Confidence cascade state:
{confidence_text}

Identify genuine contradictions between findings. Distinguish real incompatibilities from scope differences. Return ONLY valid JSON."""

HYPOTHESIS_SYSTEM = """You are a scientific hypothesis generator. Given convergent evidence, contradictions, and gaps in the current knowledge, generate novel hypotheses that:
1. Explain observed patterns
2. Resolve contradictions
3. Make testable predictions
4. Connect previously unrelated findings

Output JSON only:
{"emergent_hypotheses": [{"id": "hyp_1", "statement": "the hypothesis", "type": "explanatory|bridging|predictive|unifying", "novelty_score": 0.0-1.0, "testability_score": 0.0-1.0, "evidence_basis": [{"claim": "supporting observation", "role": "motivates|constrains|predicts"}], "predictions": [{"prediction": "what should be true if hypothesis holds", "test_method": "how to check", "expected_outcome": "what we'd see", "falsification_criterion": "what would disprove it"}], "connects_threads": ["dossier_id or topic"], "prior_probability": 0.0-1.0, "information_value": 0.0-1.0}], "frontier_summary": "one paragraph on where the field is heading"}"""

HYPOTHESIS_PROMPT = """Convergent evidence:
{convergence_text}

Active contradictions:
{contradictions_text}

Knowledge gaps:
{gaps_text}

Existing hypotheses under test:
{existing_hypotheses_text}

Generate novel, testable hypotheses that emerge from synthesizing these findings. Prioritize hypotheses that bridge multiple research threads. Return ONLY valid JSON."""

FRONTIER_SYSTEM = """You are a research frontier cartographer. Given the current state of knowledge across multiple research threads, map the frontier — where the known meets the unknown.

Output JSON only:
{"frontier_map": {"established_territory": [{"zone": "description", "confidence": 0.0-1.0, "key_claims": ["claim"]}], "active_frontiers": [{"id": "front_1", "name": "frontier name", "description": "what's being explored", "maturity": "nascent|emerging|consolidating", "key_questions": ["open question"], "promising_directions": ["direction"], "blockers": ["what's holding progress back"], "estimated_timeline": "when breakthroughs might come", "dossiers_involved": ["id"]}], "terra_incognita": [{"region": "what we don't know", "why_it_matters": "impact if solved", "prerequisites": ["what needs to happen first"]}], "paradigm_tensions": [{"tension": "description", "camps": ["position A", "position B"], "resolution_path": "how it might resolve"}]}}"""

FRONTIER_PROMPT = """Knowledge state across all threads:

Dossier summaries:
{dossiers_text}

Claim confidence distribution:
{confidence_dist_text}

Recent experimental outcomes:
{experiments_text}

Literature gaps identified:
{gaps_text}

Map the research frontier. Return ONLY valid JSON."""

NARRATIVE_SYSTEM = """You are a research narrative synthesizer. Given structured synthesis outputs (convergence patterns, contradictions, hypotheses, frontier map), compose a coherent research narrative that tells the story of what we know, what we don't, and where we're heading.

Output JSON only:
{"narrative": {"title": "compelling title", "executive_summary": "2-3 sentences", "story_arc": [{"section": "title", "content": "paragraph", "key_insight": "one sentence", "confidence_level": "high|medium|low|speculative"}], "key_takeaways": ["takeaway"], "open_questions": ["question ranked by importance"], "recommended_next_steps": [{"action": "what to do", "rationale": "why", "priority": "critical|high|medium|low", "tools_needed": ["kaleidoscope tool name"]}], "meta_confidence": 0.0-1.0}}"""

NARRATIVE_PROMPT = """Synthesis inputs:

Convergence patterns:
{convergence_text}

Contradictions:
{contradictions_text}

Emergent hypotheses:
{hypotheses_text}

Frontier map:
{frontier_text}

Compose a coherent research narrative. Return ONLY valid JSON."""


class SynthesisEngineService:
    """Cross-dossier synthesis and emergent hypothesis generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_convergence(
        self,
        dossier_ids: list[str],
        *,
        topic_filter: str | None = None,
        min_streams: int = 2,
    ) -> dict:
        """Identify convergent evidence across multiple research threads."""
        from app.clients.llm_client import LLMClient

        threads = await self._gather_threads(dossier_ids)
        claims = await self._gather_cross_claims(dossier_ids, topic_filter)
        experiments = await self._gather_experiments(dossier_ids)

        threads_text = "\n\n".join(
            f"--- Thread: {t['title']} (dossier: {t['dossier_id'][:8]}) ---\n"
            f"Summary: {t['summary'][:300]}\n"
            f"Key findings: {'; '.join(t['findings'][:5])}"
            for t in threads[:8]
        ) or "No thread summaries available"

        claims_text = "\n".join(
            f"- [{c.get('confidence', 0):.2f}] {c.get('text', '')[:120]} "
            f"(from: {c.get('source', 'unknown')[:30]})"
            for c in claims[:20]
        ) or "No cross-cutting claims"

        experiments_text = "\n".join(
            f"- {e.get('title', '?')}: {e.get('outcome', 'pending')} "
            f"(confidence: {e.get('confidence', 0):.2f})"
            for e in experiments[:10]
        ) or "No experimental results"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONVERGENCE_PROMPT.format(
                threads_text=threads_text,
                claims_text=claims_text,
                experiments_text=experiments_text,
            ),
            system=CONVERGENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        convergence = data.get("convergence_map", data)

        patterns = convergence.get("patterns", [])
        strong = [p for p in patterns if p.get("convergence_strength", 0) >= 0.7]

        return {
            "dossier_ids": dossier_ids,
            "patterns_found": len(patterns),
            "strong_patterns": len(strong),
            "convergence_map": convergence,
            "meta_confidence": convergence.get("meta_confidence", 0),
            "strongest_signal": convergence.get("strongest_signal", ""),
        }

    async def detect_contradictions(
        self,
        dossier_ids: list[str],
        *,
        include_resolved: bool = False,
    ) -> dict:
        """Find genuine contradictions between research threads."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_cross_claims(dossier_ids)
        verifications = await self._gather_verifications(dossier_ids)
        confidence_state = await self._gather_confidence_state(dossier_ids)

        claims_text = "\n".join(
            f"- [{c.get('confidence', 0):.2f}] {c.get('text', '')[:150]} "
            f"(source: {c.get('source', '?')}, method: {c.get('methodology', '?')})"
            for c in claims[:25]
        ) or "No claims available"

        verification_text = "\n".join(
            f"- {v.get('claim', '')[:80]}: {v.get('verdict', '?')} "
            f"(confidence: {v.get('confidence', 0):.2f})"
            for v in verifications[:10]
        ) or "No verification results"

        confidence_text = "\n".join(
            f"- {cs.get('claim', '')[:80]}: effective={cs.get('effective', 0):.2f}, "
            f"status={cs.get('status', '?')}"
            for cs in confidence_state[:15]
        ) or "No confidence cascade data"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTRADICTION_PROMPT.format(
                claims_text=claims_text,
                verification_text=verification_text,
                confidence_text=confidence_text,
            ),
            system=CONTRADICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        contradictions = data.get("contradictions", [])

        fundamental = [c for c in contradictions if c.get("severity") == "fundamental"]
        testable_resolutions = sum(
            len([r for r in c.get("possible_resolutions", []) if r.get("testable")])
            for c in contradictions
        )

        return {
            "dossier_ids": dossier_ids,
            "contradictions_found": len(contradictions),
            "fundamental_count": len(fundamental),
            "testable_resolutions": testable_resolutions,
            "contradictions": contradictions,
            "highest_priority": data.get("highest_priority", ""),
        }

    async def generate_hypotheses(
        self,
        dossier_ids: list[str],
        *,
        convergence: dict | None = None,
        contradictions: list | None = None,
        max_hypotheses: int = 5,
    ) -> dict:
        """Generate novel hypotheses from cross-dossier synthesis."""
        from app.clients.llm_client import LLMClient

        if not convergence:
            conv_result = await self.find_convergence(dossier_ids)
            convergence = conv_result.get("convergence_map", {})

        if contradictions is None:
            contra_result = await self.detect_contradictions(dossier_ids)
            contradictions = contra_result.get("contradictions", [])

        gaps = await self._gather_gaps(dossier_ids)
        existing = await self._gather_existing_hypotheses(dossier_ids)

        convergence_text = "\n".join(
            f"- [{p.get('convergence_strength', 0):.2f}] {p.get('thesis', '')[:120]}"
            for p in convergence.get("patterns", [])[:8]
        ) or "No convergence patterns"

        contradictions_text = "\n".join(
            f"- {c.get('claim_a', {}).get('text', '')[:60]} VS "
            f"{c.get('claim_b', {}).get('text', '')[:60]} "
            f"(type: {c.get('contradiction_type', '?')})"
            for c in contradictions[:8]
        ) or "No contradictions"

        gaps_text = "\n".join(
            f"- {g.get('description', '')[:100]} (priority: {g.get('priority', '?')})"
            for g in gaps[:8]
        ) or "No identified gaps"

        existing_text = "\n".join(
            f"- {h.get('statement', '')[:100]} (status: {h.get('status', 'untested')})"
            for h in existing[:5]
        ) or "No existing hypotheses"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HYPOTHESIS_PROMPT.format(
                convergence_text=convergence_text,
                contradictions_text=contradictions_text,
                gaps_text=gaps_text,
                existing_hypotheses_text=existing_text,
            ),
            system=HYPOTHESIS_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = self._parse_json(raw)
        hypotheses = data.get("emergent_hypotheses", [])[:max_hypotheses]

        novel = [h for h in hypotheses if h.get("novelty_score", 0) >= 0.7]
        testable = [h for h in hypotheses if h.get("testability_score", 0) >= 0.7]

        return {
            "dossier_ids": dossier_ids,
            "hypotheses_generated": len(hypotheses),
            "novel_count": len(novel),
            "testable_count": len(testable),
            "hypotheses": hypotheses,
            "frontier_summary": data.get("frontier_summary", ""),
        }

    async def map_frontier(
        self,
        dossier_ids: list[str],
    ) -> dict:
        """Map the research frontier across all threads."""
        from app.clients.llm_client import LLMClient

        threads = await self._gather_threads(dossier_ids)
        confidence_dist = await self._gather_confidence_distribution(dossier_ids)
        experiments = await self._gather_experiments(dossier_ids)
        gaps = await self._gather_gaps(dossier_ids)

        dossiers_text = "\n\n".join(
            f"--- {t['title']} ---\n{t['summary'][:200]}\n"
            f"Findings: {'; '.join(t['findings'][:3])}"
            for t in threads[:8]
        ) or "No dossier summaries"

        confidence_dist_text = "\n".join(
            f"- {cd.get('range', '?')}: {cd.get('count', 0)} claims"
            for cd in confidence_dist
        ) or "No confidence data"

        experiments_text = "\n".join(
            f"- {e.get('title', '?')}: {e.get('outcome', 'pending')}"
            for e in experiments[:8]
        ) or "No experiments"

        gaps_text = "\n".join(
            f"- {g.get('description', '')[:100]}"
            for g in gaps[:8]
        ) or "No gaps identified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FRONTIER_PROMPT.format(
                dossiers_text=dossiers_text,
                confidence_dist_text=confidence_dist_text,
                experiments_text=experiments_text,
                gaps_text=gaps_text,
            ),
            system=FRONTIER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        frontier = data.get("frontier_map", data)

        return {
            "dossier_ids": dossier_ids,
            "established_zones": len(frontier.get("established_territory", [])),
            "active_frontiers": len(frontier.get("active_frontiers", [])),
            "unknown_regions": len(frontier.get("terra_incognita", [])),
            "paradigm_tensions": len(frontier.get("paradigm_tensions", [])),
            "frontier_map": frontier,
        }

    async def synthesize_narrative(
        self,
        dossier_ids: list[str],
        *,
        convergence: dict | None = None,
        contradictions: list | None = None,
        hypotheses: list | None = None,
        frontier: dict | None = None,
    ) -> dict:
        """Compose a coherent research narrative from all synthesis outputs."""
        from app.clients.llm_client import LLMClient

        if not convergence:
            conv_result = await self.find_convergence(dossier_ids)
            convergence = conv_result.get("convergence_map", {})

        if contradictions is None:
            contra_result = await self.detect_contradictions(dossier_ids)
            contradictions = contra_result.get("contradictions", [])

        if hypotheses is None:
            hyp_result = await self.generate_hypotheses(
                dossier_ids, convergence=convergence, contradictions=contradictions
            )
            hypotheses = hyp_result.get("hypotheses", [])

        if not frontier:
            front_result = await self.map_frontier(dossier_ids)
            frontier = front_result.get("frontier_map", {})

        convergence_text = "\n".join(
            f"- {p.get('thesis', '')[:120]} (strength: {p.get('convergence_strength', 0):.2f})"
            for p in convergence.get("patterns", [])[:6]
        ) or "None found"

        contradictions_text = "\n".join(
            f"- {c.get('claim_a', {}).get('text', '')[:50]} vs "
            f"{c.get('claim_b', {}).get('text', '')[:50]}"
            for c in contradictions[:5]
        ) or "None found"

        hypotheses_text = "\n".join(
            f"- [{h.get('type', '?')}] {h.get('statement', '')[:120]} "
            f"(novelty: {h.get('novelty_score', 0):.2f})"
            for h in hypotheses[:5]
        ) or "None generated"

        frontier_text = "\n".join(
            f"- {f.get('name', '?')}: {f.get('description', '')[:80]} "
            f"(maturity: {f.get('maturity', '?')})"
            for f in frontier.get("active_frontiers", [])[:5]
        ) or "Not mapped"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_PROMPT.format(
                convergence_text=convergence_text,
                contradictions_text=contradictions_text,
                hypotheses_text=hypotheses_text,
                frontier_text=frontier_text,
            ),
            system=NARRATIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        narrative = data.get("narrative", data)

        return {
            "dossier_ids": dossier_ids,
            "narrative": narrative,
            "synthesis_inputs": {
                "convergence_patterns": len(convergence.get("patterns", [])),
                "contradictions": len(contradictions),
                "hypotheses": len(hypotheses),
                "frontier_zones": len(frontier.get("active_frontiers", [])),
            },
        }

    async def full_synthesis(
        self,
        dossier_ids: list[str],
        *,
        topic_filter: str | None = None,
    ) -> dict:
        """Run the complete synthesis pipeline and return all outputs."""
        convergence_result = await self.find_convergence(
            dossier_ids, topic_filter=topic_filter
        )
        convergence = convergence_result.get("convergence_map", {})

        contradiction_result = await self.detect_contradictions(dossier_ids)
        contradictions = contradiction_result.get("contradictions", [])

        hypothesis_result = await self.generate_hypotheses(
            dossier_ids, convergence=convergence, contradictions=contradictions
        )
        hypotheses = hypothesis_result.get("hypotheses", [])

        frontier_result = await self.map_frontier(dossier_ids)
        frontier = frontier_result.get("frontier_map", {})

        narrative_result = await self.synthesize_narrative(
            dossier_ids,
            convergence=convergence,
            contradictions=contradictions,
            hypotheses=hypotheses,
            frontier=frontier,
        )

        return {
            "dossier_ids": dossier_ids,
            "convergence": convergence_result,
            "contradictions": contradiction_result,
            "hypotheses": hypothesis_result,
            "frontier": frontier_result,
            "narrative": narrative_result,
            "tool_count": 6,
        }

    # --- Private helpers ---

    async def _gather_threads(self, dossier_ids: list[str]) -> list[dict]:
        from app.models.dossier import ResearchDossier
        from sqlalchemy import select

        threads = []
        for did in dossier_ids[:8]:
            try:
                result = await self.db.execute(
                    select(ResearchDossier).where(ResearchDossier.id == did)
                )
                dossier = result.scalar_one_or_none()
                if dossier:
                    claims_data = dossier.claims or {}
                    findings = []
                    if isinstance(claims_data, dict):
                        for k, v in list(claims_data.items())[:5]:
                            findings.append(str(v)[:100] if not isinstance(v, str) else v[:100])
                    elif isinstance(claims_data, list):
                        findings = [str(c)[:100] for c in claims_data[:5]]

                    summary = dossier.research_question or dossier.topic or ""
                    if dossier.confidence_summary:
                        summary += f" | Confidence: {dossier.confidence_summary}"

                    threads.append({
                        "dossier_id": str(dossier.id),
                        "title": dossier.topic or "Untitled",
                        "summary": summary[:400],
                        "findings": findings,
                    })
            except Exception as e:
                logger.warning("gather_thread_failed", dossier_id=did, error=str(e))
        return threads

    async def _gather_cross_claims(
        self, dossier_ids: list[str], topic_filter: str | None = None
    ) -> list[dict]:
        from app.models.claim_ledger import GlobalClaim, ClaimMention
        from sqlalchemy import select

        claims = []
        try:
            stmt = (
                select(GlobalClaim)
                .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                .where(ClaimMention.dossier_id.in_(dossier_ids))
                .distinct()
                .limit(30)
            )
            result = await self.db.execute(stmt)
            for claim in result.scalars().all():
                claims.append({
                    "text": claim.canonical_text or "",
                    "confidence": (claim.evidence_strength_score or 50) / 100.0,
                    "source": str(claim.id)[:8],
                    "methodology": claim.status or "unknown",
                    "status": claim.status,
                })
        except Exception as e:
            logger.warning("gather_claims_failed", error=str(e))

        if not claims:
            try:
                search_svc = self._get_vector_search()
                query = topic_filter or "research findings"
                results = search_svc.search(query=query, top_k=15)
                for r in results:
                    p = r.get("payload", {})
                    claims.append({
                        "text": p.get("text", p.get("title", ""))[:150],
                        "confidence": r.get("score", 0.5),
                        "source": p.get("dossier_id", "unknown")[:8],
                        "methodology": "vector_search",
                    })
            except Exception as e:
                logger.warning("gather_claims_vector_fallback_failed", error=str(e))

        return claims

    async def _gather_experiments(self, dossier_ids: list[str]) -> list[dict]:
        from app.services.search.vector_search import VectorSearchService

        experiments = []
        try:
            search_svc = VectorSearchService()
            for did in dossier_ids[:4]:
                try:
                    results = search_svc.search(query=f"experiment results {did[:8]}", top_k=3)
                    for r in results:
                        p = r.get("payload", {})
                        experiments.append({
                            "title": p.get("title", "Unknown experiment"),
                            "outcome": p.get("outcome", "unknown"),
                            "confidence": r.get("score", 0.5),
                            "dossier_id": did,
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.warning("gather_experiments_failed", error=str(e))
        return experiments[:10]

    async def _gather_verifications(self, dossier_ids: list[str]) -> list[dict]:
        verifications = []
        try:
            search_svc = self._get_vector_search()
            results = search_svc.search(query="verification result verdict", top_k=10)
            for r in results:
                p = r.get("payload", {})
                verifications.append({
                    "claim": p.get("text", p.get("title", ""))[:100],
                    "verdict": p.get("verdict", "unknown"),
                    "confidence": r.get("score", 0.5),
                })
        except Exception as e:
            logger.warning("gather_verifications_failed", error=str(e))
        return verifications

    async def _gather_confidence_state(self, dossier_ids: list[str]) -> list[dict]:
        from app.models.claim_ledger import GlobalClaim, ClaimMention
        from sqlalchemy import select

        states = []
        try:
            stmt = (
                select(GlobalClaim)
                .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                .where(ClaimMention.dossier_id.in_(dossier_ids))
                .distinct()
                .limit(20)
            )
            result = await self.db.execute(stmt)
            for claim in result.scalars().all():
                states.append({
                    "claim": (claim.canonical_text or "")[:100],
                    "effective": (claim.evidence_strength_score or 50) / 100.0,
                    "status": claim.status or "active",
                })
        except Exception:
            pass
        return states

    async def _gather_confidence_distribution(self, dossier_ids: list[str]) -> list[dict]:
        from app.models.claim_ledger import GlobalClaim, ClaimMention
        from sqlalchemy import select, func

        dist = []
        ranges = [(0, 25), (25, 50), (50, 75), (75, 100)]
        try:
            for low, high in ranges:
                stmt = (
                    select(func.count(GlobalClaim.id))
                    .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                    .where(
                        ClaimMention.dossier_id.in_(dossier_ids),
                        GlobalClaim.evidence_strength_score >= low,
                        GlobalClaim.evidence_strength_score < high,
                    )
                )
                result = await self.db.execute(stmt)
                count = result.scalar() or 0
                dist.append({"range": f"{low}-{high}%", "count": count})
        except Exception:
            dist = [{"range": "0-100%", "count": 0}]
        return dist

    async def _gather_gaps(self, dossier_ids: list[str]) -> list[dict]:
        gaps = []
        try:
            search_svc = self._get_vector_search()
            results = search_svc.search(query="literature gap unexplored", top_k=8)
            for r in results:
                p = r.get("payload", {})
                gaps.append({
                    "description": p.get("text", p.get("title", ""))[:150],
                    "priority": "high" if r.get("score", 0) > 0.7 else "medium",
                })
        except Exception as e:
            logger.warning("gather_gaps_failed", error=str(e))
        return gaps

    async def _gather_existing_hypotheses(self, dossier_ids: list[str]) -> list[dict]:
        hypotheses = []
        try:
            search_svc = self._get_vector_search()
            results = search_svc.search(query="hypothesis prediction testable", top_k=5)
            for r in results:
                p = r.get("payload", {})
                hypotheses.append({
                    "statement": p.get("text", p.get("title", ""))[:150],
                    "status": "untested",
                })
        except Exception as e:
            logger.warning("gather_hypotheses_failed", error=str(e))
        return hypotheses

    def _get_vector_search(self):
        from app.services.search.vector_search import VectorSearchService
        return VectorSearchService()

    def _parse_json(self, text: str) -> dict:
        import json
        import re

        if not text:
            return {}
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
        if not text.startswith("{"):
            start = text.find("{")
            if start >= 0:
                text = text[start:]
            else:
                return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            end = text.rfind("}")
            if end > 0:
                try:
                    return json.loads(text[: end + 1])
                except json.JSONDecodeError:
                    pass
            # Attempt to repair truncated JSON by closing open structures
            repaired = self._repair_truncated_json(text)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass
            return {}

    def _repair_truncated_json(self, text: str) -> str:
        """Attempt to close truncated JSON by balancing brackets."""
        open_braces = 0
        open_brackets = 0
        in_string = False
        escape_next = False

        for ch in text:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                open_braces += 1
            elif ch == '}':
                open_braces -= 1
            elif ch == '[':
                open_brackets += 1
            elif ch == ']':
                open_brackets -= 1

        if open_braces <= 0 and open_brackets <= 0:
            return ""

        # Truncate at last complete value
        last_comma = text.rfind(',')
        last_colon = text.rfind(':')
        # If we're mid-value after a colon, truncate to before that key-value
        if last_colon > last_comma:
            # We're in the middle of a value, cut back to last comma
            if last_comma > 0:
                text = text[:last_comma]
        elif last_comma > 0:
            text = text[:last_comma]

        # Close open structures
        text += ']' * max(0, open_brackets - text.count(']') + text.count('[') - open_brackets)
        # Recount after truncation
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        text += ']' * open_brackets + '}' * open_braces
        return text
