"""TemporalIntelligenceService — Research Evolution & Momentum Tracking.

Tracks how knowledge evolves over time, detects paradigm shifts, measures
research velocity, identifies emerging vs declining topics, and predicts
where breakthroughs are likely to come. Gives agents temporal awareness
that no other platform provides.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VELOCITY_SYSTEM = """You are a research velocity analyst. Given a timeline of claims, papers, and evidence for a topic, analyze the rate and direction of progress.

Output JSON only:
{"velocity_analysis": {"topic": "what we're tracking", "velocity_score": 0.0-1.0, "acceleration": -1.0 to 1.0, "direction": "advancing|stalling|pivoting|fragmenting|converging", "phase": "nascent|growth|plateau|decline|renaissance", "key_inflection_points": [{"date": "when", "event": "what happened", "impact": "how it changed the trajectory"}], "momentum_indicators": [{"indicator": "signal", "trend": "up|down|stable", "significance": 0.0-1.0}], "prediction": {"next_6_months": "what's likely to happen", "confidence": 0.0-1.0, "wildcards": ["unexpected things that could change everything"]}}}"""

VELOCITY_PROMPT = """Topic: {topic}

Timeline of developments:
{timeline_text}

Publication rate data:
{pub_rate_text}

Claim confidence changes over time:
{confidence_changes_text}

Recent experimental outcomes:
{experiments_text}

Analyze research velocity and predict trajectory. Return ONLY valid JSON."""

PARADIGM_SHIFT_SYSTEM = """You are a paradigm shift detector. Given the evolution of claims and evidence in a field, identify whether a paradigm shift is occurring — a fundamental change in how the field thinks about a problem.

Output JSON only:
{"paradigm_analysis": {"field": "the research area", "shift_detected": true, "shift_probability": 0.0-1.0, "old_paradigm": {"description": "the previous way of thinking", "key_assumptions": ["assumption"], "dominant_since": "timeframe"}, "new_paradigm": {"description": "the emerging way of thinking", "key_differences": ["difference"], "evidence_for": ["supporting evidence"], "first_signals": "when first signs appeared"}, "transition_stage": "pre_anomaly|anomaly_accumulation|crisis|revolution|new_normal", "resistance_factors": ["what's slowing the shift"], "adoption_indicators": [{"indicator": "signal", "current_state": "description"}], "implications": ["what this means for research strategy"]}}"""

PARADIGM_SHIFT_PROMPT = """Field: {field}

Historical claims and their evolution:
{claims_evolution_text}

Contradictions and anomalies:
{anomalies_text}

New methodologies emerging:
{methods_text}

Citation pattern changes:
{citation_text}

Detect whether a paradigm shift is occurring. Return ONLY valid JSON."""

EMERGENCE_SYSTEM = """You are an emergence detector for research topics. Given publication patterns, citation dynamics, and claim evolution, identify topics that are about to break out — the next big thing before it becomes obvious.

Output JSON only:
{"emergence_scan": {"emerging_topics": [{"id": "emg_1", "topic": "the emerging area", "emergence_score": 0.0-1.0, "signals": [{"signal": "what indicates emergence", "strength": 0.0-1.0}], "current_stage": "seed|sprout|growth|breakout", "key_papers": ["paper that started it"], "growth_rate": "description", "potential_impact": "high|transformative|moderate", "time_to_mainstream": "estimate", "connection_to_existing": "how it relates to current research"}], "declining_topics": [{"topic": "what's fading", "decline_signals": ["signal"], "reason": "why it's declining"}], "convergence_events": [{"topics": ["topic A", "topic B"], "convergence_point": "where they meet", "potential": "what could emerge from convergence"}]}}"""

EMERGENCE_PROMPT = """Current research landscape:
{landscape_text}

Recent publication patterns:
{pub_patterns_text}

New terms and concepts appearing:
{new_concepts_text}

Cross-citation patterns:
{cross_cite_text}

Identify emerging topics and declining ones. Return ONLY valid JSON."""

FORECAST_SYSTEM = """You are a research forecaster. Given the current state of a field, its velocity, emerging topics, and paradigm tensions, forecast what's likely to happen in the near and medium term.

Output JSON only:
{"forecast": {"field": "the area", "horizon": "timeframe", "predictions": [{"id": "pred_1", "prediction": "what will happen", "probability": 0.0-1.0, "timeframe": "when", "basis": "why we think this", "impact_if_true": "consequence", "early_indicators": ["what to watch for"]}], "breakthroughs_likely": [{"area": "where", "probability": 0.0-1.0, "prerequisites": ["what needs to happen first"], "blockers": ["what could prevent it"]}], "risks": [{"risk": "what could go wrong", "probability": 0.0-1.0, "mitigation": "how to prepare"}], "strategic_recommendations": [{"action": "what to do", "timing": "when", "rationale": "why"}]}}"""

FORECAST_PROMPT = """Field: {field}

Current velocity and direction:
{velocity_text}

Emerging topics:
{emergence_text}

Paradigm tensions:
{paradigm_text}

Resource and talent flows:
{resource_text}

Forecast the next 6-12 months. Return ONLY valid JSON."""


class TemporalIntelligenceService:
    """Research evolution tracking and predictive intelligence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_velocity(
        self,
        topic: str,
        *,
        dossier_id: str | None = None,
        timeframe_months: int = 12,
    ) -> dict:
        """Analyze research velocity — rate and direction of progress."""
        from app.clients.llm_client import LLMClient

        timeline = await self._build_timeline(topic, dossier_id, timeframe_months)
        pub_rate = await self._get_publication_rate(topic)
        confidence_changes = await self._get_confidence_changes(dossier_id)
        experiments = await self._get_recent_experiments(topic)

        timeline_text = "\n".join(
            f"- [{t.get('date', '?')}] {t.get('event', '')[:100]}"
            for t in timeline[:15]
        ) or "Limited timeline data"

        pub_rate_text = "\n".join(
            f"- {p.get('period', '?')}: {p.get('count', 0)} papers"
            for p in pub_rate[:6]
        ) or "Publication rate data unavailable"

        confidence_text = "\n".join(
            f"- {c.get('claim', '')[:80]}: {c.get('old', '?')} → {c.get('new', '?')}"
            for c in confidence_changes[:8]
        ) or "No confidence change data"

        experiments_text = "\n".join(
            f"- {e.get('title', '?')}: {e.get('outcome', '?')}"
            for e in experiments[:5]
        ) or "No recent experiments"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VELOCITY_PROMPT.format(
                topic=topic,
                timeline_text=timeline_text,
                pub_rate_text=pub_rate_text,
                confidence_changes_text=confidence_text,
                experiments_text=experiments_text,
            ),
            system=VELOCITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        velocity = data.get("velocity_analysis", data)

        return {
            "topic": topic,
            "velocity_score": velocity.get("velocity_score", 0),
            "acceleration": velocity.get("acceleration", 0),
            "direction": velocity.get("direction", "unknown"),
            "phase": velocity.get("phase", "unknown"),
            "inflection_points": velocity.get("key_inflection_points", []),
            "momentum_indicators": velocity.get("momentum_indicators", []),
            "prediction": velocity.get("prediction", {}),
        }

    async def detect_paradigm_shift(
        self,
        field: str,
        *,
        dossier_ids: list[str] | None = None,
    ) -> dict:
        """Detect whether a paradigm shift is occurring in a field."""
        from app.clients.llm_client import LLMClient

        claims_evolution = await self._get_claims_evolution(field, dossier_ids)
        anomalies = await self._get_anomalies(field, dossier_ids)
        methods = await self._get_new_methods(field)
        citations = await self._get_citation_changes(field)

        claims_text = "\n".join(
            f"- {c.get('claim', '')[:100]} (status: {c.get('status', '?')}, "
            f"trend: {c.get('trend', '?')})"
            for c in claims_evolution[:12]
        ) or "Limited claims evolution data"

        anomalies_text = "\n".join(
            f"- {a.get('description', '')[:100]}" for a in anomalies[:8]
        ) or "No anomalies detected"

        methods_text = "\n".join(
            f"- {m}" for m in methods[:6]
        ) or "No new methodologies noted"

        citation_text = "\n".join(
            f"- {c}" for c in citations[:6]
        ) or "No citation pattern data"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PARADIGM_SHIFT_PROMPT.format(
                field=field,
                claims_evolution_text=claims_text,
                anomalies_text=anomalies_text,
                methods_text=methods_text,
                citation_text=citation_text,
            ),
            system=PARADIGM_SHIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        analysis = data.get("paradigm_analysis", data)

        return {
            "field": field,
            "shift_detected": analysis.get("shift_detected", False),
            "shift_probability": analysis.get("shift_probability", 0),
            "transition_stage": analysis.get("transition_stage", "unknown"),
            "old_paradigm": analysis.get("old_paradigm", {}),
            "new_paradigm": analysis.get("new_paradigm", {}),
            "resistance_factors": analysis.get("resistance_factors", []),
            "implications": analysis.get("implications", []),
        }

    async def scan_emergence(
        self,
        *,
        dossier_ids: list[str] | None = None,
        field: str = "",
    ) -> dict:
        """Identify emerging and declining research topics."""
        from app.clients.llm_client import LLMClient

        landscape = await self._get_landscape(field, dossier_ids)
        pub_patterns = await self._get_pub_patterns(field)
        new_concepts = await self._get_new_concepts(field, dossier_ids)
        cross_citations = await self._get_cross_citations(field)

        landscape_text = "\n".join(
            f"- {l}" for l in landscape[:10]
        ) or "General AI/ML research landscape"

        pub_patterns_text = "\n".join(
            f"- {p}" for p in pub_patterns[:8]
        ) or "Standard publication patterns"

        new_concepts_text = "\n".join(
            f"- {c}" for c in new_concepts[:10]
        ) or "No notably new concepts"

        cross_cite_text = "\n".join(
            f"- {c}" for c in cross_citations[:6]
        ) or "No cross-citation data"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EMERGENCE_PROMPT.format(
                landscape_text=landscape_text,
                pub_patterns_text=pub_patterns_text,
                new_concepts_text=new_concepts_text,
                cross_cite_text=cross_cite_text,
            ),
            system=EMERGENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = self._parse_json(raw)
        scan = data.get("emergence_scan", data)

        emerging = scan.get("emerging_topics", [])
        breakout = [t for t in emerging if t.get("current_stage") == "breakout"]

        return {
            "field": field or "general",
            "emerging_topics": emerging,
            "breakout_count": len(breakout),
            "declining_topics": scan.get("declining_topics", []),
            "convergence_events": scan.get("convergence_events", []),
        }

    async def forecast(
        self,
        field: str,
        *,
        dossier_ids: list[str] | None = None,
        horizon_months: int = 12,
    ) -> dict:
        """Forecast research developments in the near and medium term."""
        from app.clients.llm_client import LLMClient

        velocity = await self.analyze_velocity(field, timeframe_months=horizon_months)
        emergence = await self.scan_emergence(field=field, dossier_ids=dossier_ids)
        paradigm = await self.detect_paradigm_shift(field, dossier_ids=dossier_ids)

        velocity_text = (
            f"Velocity: {velocity.get('velocity_score', 0):.2f}, "
            f"Direction: {velocity.get('direction', '?')}, "
            f"Phase: {velocity.get('phase', '?')}, "
            f"Acceleration: {velocity.get('acceleration', 0):.2f}"
        )

        emergence_text = "\n".join(
            f"- [{t.get('emergence_score', 0):.2f}] {t.get('topic', '')[:80]}"
            for t in emergence.get("emerging_topics", [])[:5]
        ) or "No emerging topics"

        paradigm_text = (
            f"Shift detected: {paradigm.get('shift_detected', False)}, "
            f"Stage: {paradigm.get('transition_stage', '?')}, "
            f"Probability: {paradigm.get('shift_probability', 0):.2f}"
        )

        resource_text = "Resource flow data not available — infer from publication patterns"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FORECAST_PROMPT.format(
                field=field,
                velocity_text=velocity_text,
                emergence_text=emergence_text,
                paradigm_text=paradigm_text,
                resource_text=resource_text,
            ),
            system=FORECAST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        forecast = data.get("forecast", data)

        predictions = forecast.get("predictions", [])
        high_conf = [p for p in predictions if p.get("probability", 0) >= 0.7]

        return {
            "field": field,
            "horizon_months": horizon_months,
            "predictions": predictions,
            "high_confidence_predictions": len(high_conf),
            "breakthroughs_likely": forecast.get("breakthroughs_likely", []),
            "risks": forecast.get("risks", []),
            "strategic_recommendations": forecast.get("strategic_recommendations", []),
            "inputs": {
                "velocity": velocity.get("velocity_score", 0),
                "direction": velocity.get("direction", ""),
                "shift_probability": paradigm.get("shift_probability", 0),
                "emerging_topics": len(emergence.get("emerging_topics", [])),
            },
        }

    # --- Private helpers ---

    async def _build_timeline(
        self, topic: str, dossier_id: str | None, months: int
    ) -> list[dict]:
        timeline = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                result = await self.db.execute(
                    select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                )
                dossier = result.scalar_one_or_none()
                if dossier:
                    memory = dossier.memory_log or []
                    for entry in memory[-15:]:
                        if isinstance(entry, dict):
                            timeline.append({
                                "date": entry.get("timestamp", "unknown"),
                                "event": entry.get("action", entry.get("event", str(entry)[:100])),
                            })
                        elif isinstance(entry, str):
                            timeline.append({"date": "unknown", "event": entry[:100]})
            except Exception:
                pass

        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{topic} recent development breakthrough", top_k=10)
            for r in results:
                p = r.get("payload", {})
                timeline.append({
                    "date": p.get("published_date", p.get("year", "recent")),
                    "event": p.get("title", p.get("text", ""))[:100],
                })
        except Exception:
            pass
        return timeline

    async def _get_publication_rate(self, topic: str) -> list[dict]:
        try:
            from app.clients.openalex import OpenAlexClient
            client = OpenAlexClient()
            results = await client.search_works(topic, per_page=50)
            from collections import Counter
            years = Counter()
            for work in results.get("results", []):
                year = work.get("publication_year")
                if year:
                    years[year] += 1
            return [
                {"period": str(y), "count": c}
                for y, c in sorted(years.items(), reverse=True)[:6]
            ]
        except Exception:
            return []

    async def _get_confidence_changes(self, dossier_id: str | None) -> list[dict]:
        if not dossier_id:
            return []
        changes = []
        try:
            from app.models.claim_ledger import ClaimConfidenceEvent, GlobalClaim, ClaimMention
            from sqlalchemy import select
            stmt = (
                select(ClaimConfidenceEvent)
                .join(GlobalClaim, GlobalClaim.id == ClaimConfidenceEvent.claim_id)
                .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                .where(ClaimMention.dossier_id == dossier_id)
                .order_by(ClaimConfidenceEvent.created_at.desc())
                .limit(10)
            )
            result = await self.db.execute(stmt)
            for event in result.scalars().all():
                changes.append({
                    "claim": str(event.claim_id)[:8],
                    "old": event.old_confidence,
                    "new": event.new_confidence,
                })
        except Exception:
            pass
        return changes

    async def _get_recent_experiments(self, topic: str) -> list[dict]:
        experiments = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{topic} experiment result", top_k=5)
            for r in results:
                p = r.get("payload", {})
                experiments.append({
                    "title": p.get("title", "")[:80],
                    "outcome": p.get("outcome", "unknown"),
                })
        except Exception:
            pass
        return experiments

    async def _get_claims_evolution(
        self, field: str, dossier_ids: list[str] | None
    ) -> list[dict]:
        claims = []
        try:
            from app.models.claim_ledger import GlobalClaim
            from sqlalchemy import select
            stmt = select(GlobalClaim).order_by(GlobalClaim.created_at.desc()).limit(15)
            result = await self.db.execute(stmt)
            for claim in result.scalars().all():
                claims.append({
                    "claim": (claim.canonical_text or "")[:100],
                    "status": claim.status or "active",
                    "trend": "stable",
                })
        except Exception:
            pass
        return claims

    async def _get_anomalies(self, field: str, dossier_ids: list[str] | None) -> list[dict]:
        anomalies = []
        try:
            from app.models.claim_ledger import GlobalClaim
            from sqlalchemy import select
            stmt = (
                select(GlobalClaim)
                .where(GlobalClaim.status == "disputed")
                .limit(8)
            )
            result = await self.db.execute(stmt)
            for claim in result.scalars().all():
                anomalies.append({
                    "description": f"Disputed: {(claim.canonical_text or '')[:100]}"
                })
        except Exception:
            pass
        return anomalies

    async def _get_new_methods(self, field: str) -> list[str]:
        methods = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{field} novel method approach technique", top_k=5)
            for r in results:
                p = r.get("payload", {})
                methods.append(p.get("title", p.get("text", ""))[:100])
        except Exception:
            pass
        return methods

    async def _get_citation_changes(self, field: str) -> list[str]:
        return []

    async def _get_landscape(self, field: str, dossier_ids: list[str] | None) -> list[str]:
        landscape = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{field} overview landscape state of the art", top_k=8)
            for r in results:
                p = r.get("payload", {})
                landscape.append(p.get("title", p.get("text", ""))[:120])
        except Exception:
            pass
        return landscape

    async def _get_pub_patterns(self, field: str) -> list[str]:
        try:
            rate = await self._get_publication_rate(field)
            return [f"{p['period']}: {p['count']} papers" for p in rate]
        except Exception:
            return []

    async def _get_new_concepts(self, field: str, dossier_ids: list[str] | None) -> list[str]:
        concepts = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{field} new concept framework paradigm", top_k=8)
            for r in results:
                p = r.get("payload", {})
                concepts.append(p.get("title", p.get("text", ""))[:100])
        except Exception:
            pass
        return concepts

    async def _get_cross_citations(self, field: str) -> list[str]:
        return []

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
            # Repair truncated JSON
            repaired = self._repair_json(text)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass
            return {}

    def _repair_json(self, text: str) -> str:
        last_comma = text.rfind(',')
        if last_comma > 0:
            text = text[:last_comma]
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        text += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
        return text
