"""StrategyOptimizerService — Meta-Cognitive Research Strategy Engine.

Helps agents decide what to do next by analyzing the current epistemic state,
identifying the highest-value actions, detecting cognitive biases in the
research process, and optimizing the exploration-exploitation tradeoff.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NEXT_ACTION_SYSTEM = """You are a research strategy optimizer. Given the current state of knowledge (claims, confidence levels, gaps, contradictions, experiments), determine the single highest-value next action an AI research agent should take.

Consider:
- Information value: which action would most reduce uncertainty?
- Risk: which claims are most fragile and need verification?
- Opportunity: where are the biggest gaps that could yield breakthroughs?
- Efficiency: what's the best use of limited compute/API budget?

Output JSON only:
{"optimal_action": {"action": "specific tool call or research step", "tool_name": "kaleidoscope tool to use", "arguments": {"key": "value"}, "rationale": "why this is the highest-value action right now", "expected_information_gain": 0.0-1.0, "urgency": "critical|high|medium|low", "alternatives": [{"action": "alternative", "tool_name": "tool", "rationale": "why this is second-best", "information_gain": 0.0-1.0}], "what_to_do_after": "the logical next step after this action completes", "budget_estimate": "low|medium|high"}}"""

NEXT_ACTION_PROMPT = """Current epistemic state:

Dossier: {dossier_summary}

Claims ({claim_count} total):
- High confidence: {high_conf_count}
- Medium confidence: {med_conf_count}
- Low confidence: {low_conf_count}
- Disputed: {disputed_count}

Active contradictions: {contradictions_count}
Open questions: {open_questions_text}
Knowledge gaps: {gaps_text}
Recent actions taken: {recent_actions_text}
Experiments pending: {experiments_text}

Available tools: {tools_summary}

What is the single highest-value next action? Return ONLY valid JSON."""

BIAS_DETECT_SYSTEM = """You are a cognitive bias detector for research processes. Given a research history (what was searched, what was found, what was concluded), identify systematic biases that may have distorted the conclusions.

Output JSON only:
{"bias_analysis": {"biases_detected": [{"id": "bias_1", "type": "confirmation|anchoring|availability|survivorship|publication|authority|framing|sunk_cost|bandwagon|dunning_kruger", "description": "how this bias manifests in the research", "evidence": ["specific example from the research history"], "severity": "critical|significant|minor", "affected_claims": ["claim that may be distorted"], "debiasing_action": "what to do to correct for this"}], "overall_bias_risk": 0.0-1.0, "most_compromised_conclusion": "the conclusion most likely distorted by bias", "debiasing_protocol": [{"step": 1, "action": "what to do", "tool": "kaleidoscope tool to use"}]}}"""

BIAS_DETECT_PROMPT = """Research history to analyze for bias:

Search queries used:
{searches_text}

Papers found and selected:
{papers_text}

Papers excluded or ignored:
{excluded_text}

Claims extracted:
{claims_text}

Conclusions reached:
{conclusions_text}

Methodology choices:
{methodology_text}

Detect cognitive biases in this research process. Return ONLY valid JSON."""

EXPLORE_EXPLOIT_SYSTEM = """You are an exploration-exploitation optimizer for research. Given the current knowledge state, determine the optimal balance between:
- EXPLORE: seeking new information in unknown areas (high variance, potential breakthroughs)
- EXPLOIT: deepening understanding in known areas (low variance, reliable progress)

Output JSON only:
{"strategy": {"recommended_balance": {"explore_pct": 0-100, "exploit_pct": 0-100}, "rationale": "why this balance", "current_phase": "early_exploration|focused_exploration|balanced|exploitation_heavy|convergence", "explore_actions": [{"action": "what to explore", "tool": "tool_name", "expected_value": 0.0-1.0, "risk": "low|medium|high"}], "exploit_actions": [{"action": "what to deepen", "tool": "tool_name", "expected_value": 0.0-1.0, "certainty_gain": 0.0-1.0}], "pivot_signals": ["when to shift the balance"], "diminishing_returns_warning": "areas where more work won't help much"}}"""

EXPLORE_EXPLOIT_PROMPT = """Knowledge state:

Coverage score: {coverage_score}/100
Confidence distribution: {confidence_dist}
Claims: {claim_count} total, {disputed_count} disputed
Gaps identified: {gaps_count}
Experiments completed: {experiments_done}
Research age: {research_age}

Recent trajectory:
{trajectory_text}

Frontier state:
{frontier_text}

Optimize the explore/exploit balance. Return ONLY valid JSON."""

PORTFOLIO_SYSTEM = """You are a research portfolio optimizer. Given multiple active research threads, optimize resource allocation across them based on expected value, risk, and diversification.

Output JSON only:
{"portfolio": {"allocations": [{"thread": "research thread name", "dossier_id": "id", "allocation_pct": 0-100, "rationale": "why this allocation", "expected_value": 0.0-1.0, "risk": "low|medium|high", "status": "active|paused|completed|blocked"}], "rebalancing_needed": true, "rebalancing_actions": [{"action": "what to change", "from_thread": "reduce this", "to_thread": "increase this", "rationale": "why"}], "portfolio_health": 0.0-1.0, "diversification_score": 0.0-1.0, "concentration_risk": "description of over-concentration"}}"""

PORTFOLIO_PROMPT = """Active research threads:

{threads_text}

Resource constraints:
- API budget: {budget}
- Time horizon: {horizon}
- Parallel capacity: {capacity}

Recent outcomes:
{outcomes_text}

Optimize resource allocation across threads. Return ONLY valid JSON."""


class StrategyOptimizerService:
    """Meta-cognitive research strategy optimization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_next_action(
        self,
        dossier_id: str,
    ) -> dict:
        """Determine the single highest-value next action for a research dossier."""
        from app.clients.llm_client import LLMClient

        state = await self._get_epistemic_state(dossier_id)

        tools_summary = (
            "search_papers, extract_claims, claim_confidence_update, "
            "red_team_steelman, synthesis_convergence, experiment_compile, "
            "lab_run_compile, temporal_velocity, literature_gap_detect, "
            "decision_compile, evidence_sufficiency_audit"
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NEXT_ACTION_PROMPT.format(
                dossier_summary=state.get("summary", ""),
                claim_count=state.get("claim_count", 0),
                high_conf_count=state.get("high_conf", 0),
                med_conf_count=state.get("med_conf", 0),
                low_conf_count=state.get("low_conf", 0),
                disputed_count=state.get("disputed", 0),
                contradictions_count=state.get("contradictions", 0),
                open_questions_text=state.get("open_questions_text", "None"),
                gaps_text=state.get("gaps_text", "None identified"),
                recent_actions_text=state.get("recent_actions_text", "None recorded"),
                experiments_text=state.get("experiments_text", "None pending"),
                tools_summary=tools_summary,
            ),
            system=NEXT_ACTION_SYSTEM,
            max_tokens=2048,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        action = data.get("optimal_action", data)

        return {
            "dossier_id": dossier_id,
            "recommended_action": action.get("action", ""),
            "tool_name": action.get("tool_name", ""),
            "arguments": action.get("arguments", {}),
            "rationale": action.get("rationale", ""),
            "expected_information_gain": action.get("expected_information_gain", 0),
            "urgency": action.get("urgency", "medium"),
            "alternatives": action.get("alternatives", []),
            "what_to_do_after": action.get("what_to_do_after", ""),
        }

    async def detect_bias(
        self,
        dossier_id: str,
    ) -> dict:
        """Detect cognitive biases in the research process."""
        from app.clients.llm_client import LLMClient

        history = await self._get_research_history(dossier_id)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIAS_DETECT_PROMPT.format(
                searches_text=history.get("searches_text", "No search history"),
                papers_text=history.get("papers_text", "No papers recorded"),
                excluded_text=history.get("excluded_text", "No exclusions recorded"),
                claims_text=history.get("claims_text", "No claims"),
                conclusions_text=history.get("conclusions_text", "No conclusions"),
                methodology_text=history.get("methodology_text", "Not documented"),
            ),
            system=BIAS_DETECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        analysis = data.get("bias_analysis", data)

        biases = analysis.get("biases_detected", [])
        critical = [b for b in biases if b.get("severity") == "critical"]

        return {
            "dossier_id": dossier_id,
            "biases_detected": len(biases),
            "critical_biases": len(critical),
            "biases": biases,
            "overall_bias_risk": analysis.get("overall_bias_risk", 0),
            "most_compromised": analysis.get("most_compromised_conclusion", ""),
            "debiasing_protocol": analysis.get("debiasing_protocol", []),
        }

    async def optimize_explore_exploit(
        self,
        dossier_id: str,
    ) -> dict:
        """Optimize the exploration-exploitation balance."""
        from app.clients.llm_client import LLMClient

        state = await self._get_epistemic_state(dossier_id)
        trajectory = await self._get_trajectory(dossier_id)
        frontier = await self._get_frontier_state(dossier_id)

        confidence_dist = (
            f"High(>0.7): {state.get('high_conf', 0)}, "
            f"Med(0.4-0.7): {state.get('med_conf', 0)}, "
            f"Low(<0.4): {state.get('low_conf', 0)}"
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPLORE_EXPLOIT_PROMPT.format(
                coverage_score=state.get("coverage_score", 0),
                confidence_dist=confidence_dist,
                claim_count=state.get("claim_count", 0),
                disputed_count=state.get("disputed", 0),
                gaps_count=state.get("gaps_count", 0),
                experiments_done=state.get("experiments_done", 0),
                research_age=state.get("research_age", "unknown"),
                trajectory_text=trajectory,
                frontier_text=frontier,
            ),
            system=EXPLORE_EXPLOIT_SYSTEM,
            max_tokens=2048,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        strategy = data.get("strategy", data)

        return {
            "dossier_id": dossier_id,
            "recommended_balance": strategy.get("recommended_balance", {}),
            "current_phase": strategy.get("current_phase", "unknown"),
            "explore_actions": strategy.get("explore_actions", []),
            "exploit_actions": strategy.get("exploit_actions", []),
            "pivot_signals": strategy.get("pivot_signals", []),
            "diminishing_returns_warning": strategy.get("diminishing_returns_warning", ""),
        }

    async def optimize_portfolio(
        self,
        dossier_ids: list[str],
        *,
        budget: str = "moderate",
        horizon: str = "1 week",
        capacity: int = 3,
    ) -> dict:
        """Optimize resource allocation across multiple research threads."""
        from app.clients.llm_client import LLMClient

        threads = await self._get_thread_summaries(dossier_ids)
        outcomes = await self._get_recent_outcomes(dossier_ids)

        threads_text = "\n\n".join(
            f"--- {t['title']} (dossier: {t['id'][:8]}) ---\n"
            f"Status: {t['status']}\n"
            f"Coverage: {t['coverage']}/100\n"
            f"Claims: {t['claims']}, Gaps: {t['gaps']}"
            for t in threads
        ) or "No active threads"

        outcomes_text = "\n".join(
            f"- {o}" for o in outcomes[:8]
        ) or "No recent outcomes"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PORTFOLIO_PROMPT.format(
                threads_text=threads_text,
                budget=budget,
                horizon=horizon,
                capacity=capacity,
                outcomes_text=outcomes_text,
            ),
            system=PORTFOLIO_SYSTEM,
            max_tokens=2048,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        portfolio = data.get("portfolio", data)

        return {
            "dossier_ids": dossier_ids,
            "allocations": portfolio.get("allocations", []),
            "rebalancing_needed": portfolio.get("rebalancing_needed", False),
            "rebalancing_actions": portfolio.get("rebalancing_actions", []),
            "portfolio_health": portfolio.get("portfolio_health", 0),
            "diversification_score": portfolio.get("diversification_score", 0),
            "concentration_risk": portfolio.get("concentration_risk", ""),
        }

    # --- Private helpers ---

    async def _get_epistemic_state(self, dossier_id: str) -> dict:
        state = {
            "summary": "", "claim_count": 0, "high_conf": 0, "med_conf": 0,
            "low_conf": 0, "disputed": 0, "contradictions": 0,
            "open_questions_text": "None", "gaps_text": "None",
            "recent_actions_text": "None", "experiments_text": "None",
            "coverage_score": 0, "gaps_count": 0, "experiments_done": 0,
            "research_age": "unknown",
        }
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            result = await self.db.execute(
                select(ResearchDossier).where(ResearchDossier.id == dossier_id)
            )
            dossier = result.scalar_one_or_none()
            if dossier:
                state["summary"] = f"{dossier.topic} — {dossier.research_question or ''}"
                state["coverage_score"] = dossier.coverage_score or 0

                claims = dossier.claims or {}
                state["claim_count"] = len(claims) if isinstance(claims, (dict, list)) else 0

                gaps = dossier.gaps or {}
                state["gaps_count"] = len(gaps) if isinstance(gaps, (dict, list)) else 0
                if isinstance(gaps, dict):
                    state["gaps_text"] = "\n".join(
                        f"- {v}" for v in list(gaps.values())[:5]
                    ) or "None"
                elif isinstance(gaps, list):
                    state["gaps_text"] = "\n".join(
                        f"- {g}" for g in gaps[:5]
                    ) or "None"

                oq = dossier.open_questions or []
                state["open_questions_text"] = "\n".join(
                    f"- {q}" for q in oq[:5]
                ) or "None"

                memory = dossier.memory_log or []
                state["recent_actions_text"] = "\n".join(
                    f"- {str(m)[:80]}" for m in memory[-5:]
                ) or "None"

                if dossier.created_at:
                    age = datetime.now(timezone.utc) - dossier.created_at.replace(tzinfo=timezone.utc)
                    state["research_age"] = f"{age.days} days"
        except Exception as e:
            logger.warning("get_epistemic_state_failed", error=str(e))

        try:
            from app.models.claim_ledger import GlobalClaim, ClaimMention
            from sqlalchemy import select, func
            stmt = (
                select(GlobalClaim)
                .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                .where(ClaimMention.dossier_id == dossier_id)
            )
            result = await self.db.execute(stmt)
            for claim in result.scalars().all():
                score = (claim.evidence_strength_score or 50) / 100.0
                if score >= 0.7:
                    state["high_conf"] += 1
                elif score >= 0.4:
                    state["med_conf"] += 1
                else:
                    state["low_conf"] += 1
                if claim.status == "disputed":
                    state["disputed"] += 1
            state["claim_count"] = state["high_conf"] + state["med_conf"] + state["low_conf"]
        except Exception:
            pass

        return state

    async def _get_research_history(self, dossier_id: str) -> dict:
        history = {
            "searches_text": "No search history",
            "papers_text": "No papers recorded",
            "excluded_text": "No exclusions",
            "claims_text": "No claims",
            "conclusions_text": "No conclusions",
            "methodology_text": "Not documented",
        }
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            result = await self.db.execute(
                select(ResearchDossier).where(ResearchDossier.id == dossier_id)
            )
            dossier = result.scalar_one_or_none()
            if dossier:
                papers = dossier.papers_seen or {}
                if isinstance(papers, dict):
                    history["papers_text"] = "\n".join(
                        f"- {v}" if isinstance(v, str) else f"- {k}"
                        for k, v in list(papers.items())[:10]
                    ) or "No papers"

                excluded = dossier.papers_excluded or {}
                if isinstance(excluded, dict):
                    history["excluded_text"] = "\n".join(
                        f"- {k}: {v}" for k, v in list(excluded.items())[:5]
                    ) or "No exclusions"

                claims = dossier.claims or {}
                if isinstance(claims, dict):
                    history["claims_text"] = "\n".join(
                        f"- {v}" if isinstance(v, str) else f"- {k}"
                        for k, v in list(claims.items())[:8]
                    ) or "No claims"

                failed = dossier.failed_searches or []
                history["searches_text"] = "\n".join(
                    f"- {s}" for s in failed[:5]
                ) or "No failed searches recorded"

                memory = dossier.memory_log or []
                history["methodology_text"] = "\n".join(
                    f"- {str(m)[:80]}" for m in memory[-8:]
                ) or "Not documented"
        except Exception:
            pass
        return history

    async def _get_trajectory(self, dossier_id: str) -> str:
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            result = await self.db.execute(
                select(ResearchDossier).where(ResearchDossier.id == dossier_id)
            )
            dossier = result.scalar_one_or_none()
            if dossier and dossier.memory_log:
                return "\n".join(f"- {str(m)[:80]}" for m in dossier.memory_log[-10:])
        except Exception:
            pass
        return "No trajectory data"

    async def _get_frontier_state(self, dossier_id: str) -> str:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query="frontier unknown gap unexplored", top_k=5)
            return "\n".join(
                f"- {r.get('payload', {}).get('title', r.get('payload', {}).get('text', ''))[:80]}"
                for r in results
            )
        except Exception:
            return "Frontier state unavailable"

    async def _get_thread_summaries(self, dossier_ids: list[str]) -> list[dict]:
        threads = []
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            for did in dossier_ids[:8]:
                result = await self.db.execute(
                    select(ResearchDossier).where(ResearchDossier.id == did)
                )
                dossier = result.scalar_one_or_none()
                if dossier:
                    claims = dossier.claims or {}
                    gaps = dossier.gaps or {}
                    threads.append({
                        "id": str(dossier.id),
                        "title": dossier.topic or "Untitled",
                        "status": dossier.status or "active",
                        "coverage": dossier.coverage_score or 0,
                        "claims": len(claims) if isinstance(claims, (dict, list)) else 0,
                        "gaps": len(gaps) if isinstance(gaps, (dict, list)) else 0,
                    })
        except Exception:
            pass
        return threads

    async def _get_recent_outcomes(self, dossier_ids: list[str]) -> list[str]:
        outcomes = []
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            for did in dossier_ids[:4]:
                result = await self.db.execute(
                    select(ResearchDossier).where(ResearchDossier.id == did)
                )
                dossier = result.scalar_one_or_none()
                if dossier and dossier.memory_log:
                    for m in dossier.memory_log[-3:]:
                        outcomes.append(f"[{dossier.topic[:20]}] {str(m)[:80]}")
        except Exception:
            pass
        return outcomes

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
            last_comma = text.rfind(',')
            if last_comma > 0:
                text = text[:last_comma]
            open_braces = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')
            text += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {}
