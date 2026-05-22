"""ExperimentCompilerService — Prospective Experiment Compiler.

Turns unresolved claims, rival theses, or fragile decisions into ranked,
executable experiments designed to maximally change the system's beliefs.
The forward-facing half of the research loop.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERIMENT_SYSTEM = """You are an experiment designer for research intelligence. Given unresolved claims, rival theses, or a fragile decision, design a precise experiment or evaluation protocol that would maximally resolve the uncertainty.

Rules:
- Design for maximum information gain, not just confirmation
- Specify clear falsification criteria
- Include confounder controls
- Be specific about datasets, benchmarks, metrics, and success thresholds
- Prefer smaller, faster experiments that still discriminate

Output JSON:
{"experiments": [{"id": "exp_1", "title": "short title", "hypothesis": "one sentence", "intervention": "what to do", "control": "baseline comparison", "datasets_or_benchmarks": ["name"], "metrics": ["metric"], "success_criteria": "threshold", "falsification_criteria": "what would disprove", "confounders_controlled": ["confounder"], "estimated_effort": "low|medium|high", "estimated_duration": "timeframe", "expected_information_gain": 0.0-1.0, "resolves_claims": ["claim_id"], "decision_impact": "how this changes the decision"}]}"""

EXPERIMENT_PROMPT = """Research context:
Question: {question}

Unresolved claims:
{claims_text}

Rival theses (if any):
{theses_text}

Causal model nodes (if any):
{causal_text}

Current decision (if any):
{decision_text}

Constraints: {constraints}

Design {n_experiments} experiments that would maximally resolve this uncertainty. Return ONLY valid JSON."""

DISCRIMINATE_SYSTEM = """You are an experiment designer specializing in discriminating between rival hypotheses. Given two or more competing theses and the crux claims that separate them, design the smallest possible experiment that would decisively favor one thesis over the others.

Output JSON:
{"experiment": {"id": "exp_disc_1", "title": "short title", "discriminates_between": ["thesis_a", "thesis_b"], "crux_targeted": "the crux claim this resolves", "hypothesis_a_predicts": "what thesis A expects", "hypothesis_b_predicts": "what thesis B expects", "protocol": {"intervention": "what to do", "control": "baseline", "datasets_or_benchmarks": ["name"], "metrics": ["metric"], "sample_size_or_scale": "description", "duration": "timeframe"}, "decision_rule": "if metric > X then thesis A, else thesis B", "power_analysis": "why this sample/scale is sufficient", "confounders": ["confounder and how controlled"], "expected_information_gain": 0.0-1.0, "effort": "low|medium|high"}}"""

DISCRIMINATE_PROMPT = """Thesis A: {thesis_a}
Thesis B: {thesis_b}

Crux claims (what separates them):
{cruxes_text}

Available evidence so far:
{evidence_text}

Design the smallest experiment that decisively discriminates. Return ONLY valid JSON."""

PORTFOLIO_SYSTEM = """You are a research portfolio optimizer. Given candidate experiments, a budget, and objectives, rank and select experiments to maximize total expected information gain within constraints.

Output JSON:
{"portfolio": [{"experiment_id": "id", "priority": 1, "rationale": "why this first", "expected_information_gain": 0.0-1.0, "decision_impact_score": 0.0-1.0, "cost_score": 0.0-1.0, "composite_score": 0.0-1.0}], "total_expected_gain": 0.0-1.0, "budget_utilization": 0.0-1.0, "uncovered_uncertainties": ["what remains unresolved"]}"""

PORTFOLIO_PROMPT = """Candidate experiments:
{experiments_text}

Budget constraints: {budget}
Objective: {objective}
Max experiments to select: {max_select}

Rank and select the optimal portfolio. Return ONLY valid JSON."""

RESULT_SYSTEM = """You are a research result interpreter. Given an experiment's protocol, its results, and the claims/decisions it was designed to resolve, determine what changed: which claims are strengthened/weakened, which theses won/lost, and whether any decision should be re-evaluated.

Output JSON:
{"interpretation": {"outcome": "confirmed|refuted|inconclusive", "confidence": 0.0-1.0, "claims_strengthened": [{"claim_id": "id", "delta": 0.0-1.0, "reason": "why"}], "claims_weakened": [{"claim_id": "id", "delta": 0.0-1.0, "reason": "why"}], "thesis_impact": {"winning_thesis": "or null", "losing_thesis": "or null", "reason": "why"}, "decision_impact": {"should_re_evaluate": true, "reason": "why"}, "new_questions": ["question raised by results"], "follow_up_needed": true, "follow_up_reason": "why"}}"""

RESULT_PROMPT = """Experiment: {experiment_title}
Hypothesis: {hypothesis}
Protocol: {protocol}

Results:
{results_text}

Original claims this was designed to resolve:
{claims_text}

Original decision context:
{decision_text}

Interpret the results. Return ONLY valid JSON."""


class ExperimentCompilerService:
    """Compiles uncertainty into executable experiment protocols."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_experiments(
        self,
        dossier_id: str,
        *,
        question: str | None = None,
        focus_claim_ids: list[str] | None = None,
        decision_id: str | None = None,
        n_experiments: int = 3,
        constraints: dict | None = None,
    ) -> dict:
        """Compile experiment plans from dossier uncertainty."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_unresolved_claims(dossier_id, focus_claim_ids)
        theses = await self._get_rival_theses(dossier_id, question)
        causal_info = await self._get_causal_context(dossier_id, question)
        decision_info = await self._get_decision_context(dossier_id, decision_id)

        if not question and decision_info:
            question = decision_info.get("decision_question", "")
        if not question and claims:
            question = claims[0].get("text", "")[:100]
        if not question:
            return {"error": "No question or claims to design experiments for"}

        claims_text = "\n".join(
            f"- [{c.get('claim_id', '')[:8]}] {c['text'][:120]} (confidence={c.get('confidence', 0):.2f})"
            for c in claims[:10]
        ) or "None identified"
        theses_text = "\n".join(
            f"- {t.get('thesis', '')[:100]}" for t in theses[:4]
        ) or "None"
        causal_text = "\n".join(
            f"- {n.get('label', '')}: {n.get('role', '')} ({n.get('type', '')})"
            for n in causal_info[:6]
        ) or "None available"
        decision_text = (
            f"Question: {decision_info.get('decision_question', '')}\n"
            f"Recommended: {decision_info.get('recommended_option', {}).get('title', 'None')}\n"
            f"Confidence: {decision_info.get('decision_confidence', 0)}"
            if decision_info else "No active decision"
        )
        constraints_text = str(constraints or {"budget": "medium", "timeline": "flexible"})

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERIMENT_PROMPT.format(
                question=question,
                claims_text=claims_text,
                theses_text=theses_text,
                causal_text=causal_text,
                decision_text=decision_text,
                constraints=constraints_text,
                n_experiments=n_experiments,
            ),
            system=EXPERIMENT_SYSTEM,
            max_tokens=3072,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        experiments = data.get("experiments", [])

        for exp in experiments:
            exp["experiment_id"] = exp.get("id", str(uuid.uuid4())[:8])
            exp["dossier_id"] = dossier_id
            exp["status"] = "proposed"
            exp["compiled_at"] = datetime.now(timezone.utc).isoformat()

        experiments.sort(
            key=lambda e: e.get("expected_information_gain", 0), reverse=True
        )

        return {
            "dossier_id": dossier_id,
            "question": question,
            "experiments": experiments,
            "total_expected_gain": sum(
                e.get("expected_information_gain", 0) for e in experiments
            ),
            "claims_targeted": len(claims),
            "theses_considered": len(theses),
        }

    async def discriminate(
        self,
        dossier_id: str,
        *,
        thesis_a: str,
        thesis_b: str,
        crux_claim_ids: list[str] | None = None,
    ) -> dict:
        """Design the smallest experiment to discriminate between rival theses."""
        from app.clients.llm_client import LLMClient

        cruxes = await self._get_crux_claims(dossier_id, crux_claim_ids)
        evidence = await self._gather_evidence_summary(dossier_id)

        cruxes_text = "\n".join(
            f"- {c.get('text', '')[:120]}" for c in cruxes[:5]
        ) or "No specific cruxes identified"
        evidence_text = "\n".join(
            f"- {e.get('text', '')[:100]} (strength={e.get('strength', 0):.0f})"
            for e in evidence[:8]
        ) or "Limited evidence"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISCRIMINATE_PROMPT.format(
                thesis_a=thesis_a,
                thesis_b=thesis_b,
                cruxes_text=cruxes_text,
                evidence_text=evidence_text,
            ),
            system=DISCRIMINATE_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        experiment = data.get("experiment", data)

        experiment["dossier_id"] = dossier_id
        experiment["status"] = "proposed"
        experiment["type"] = "discriminating"
        experiment["compiled_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "dossier_id": dossier_id,
            "thesis_a": thesis_a,
            "thesis_b": thesis_b,
            "experiment": experiment,
            "cruxes_targeted": len(cruxes),
        }

    async def compile_portfolio(
        self,
        dossier_id: str,
        *,
        experiments: list[dict] | None = None,
        budget: str = "medium",
        objective: str = "maximize_information_gain",
        max_select: int = 3,
    ) -> dict:
        """Build a budgeted portfolio of experiments ranked by expected information gain."""
        from app.clients.llm_client import LLMClient

        if not experiments:
            compiled = await self.compile_experiments(
                dossier_id, n_experiments=5
            )
            experiments = compiled.get("experiments", [])

        if not experiments:
            return {"error": "No experiments to rank", "dossier_id": dossier_id}

        experiments_text = "\n".join(
            f"- [{e.get('experiment_id', e.get('id', f'exp_{i}'))}] "
            f"{e.get('title', 'Untitled')}: {e.get('hypothesis', '')[:80]} "
            f"(effort={e.get('estimated_effort', '?')}, EIG={e.get('expected_information_gain', 0):.2f})"
            for i, e in enumerate(experiments)
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PORTFOLIO_PROMPT.format(
                experiments_text=experiments_text,
                budget=budget,
                objective=objective,
                max_select=max_select,
            ),
            system=PORTFOLIO_SYSTEM,
            max_tokens=1536,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        portfolio = data.get("portfolio", [])

        exp_map = {}
        for i, e in enumerate(experiments):
            eid = e.get("experiment_id", e.get("id", f"exp_{i}"))
            exp_map[eid] = e
            exp_map[f"exp_{i+1}"] = e
            exp_map[f"exp_{i}"] = e
            exp_map[str(i)] = e
            exp_map[str(i+1)] = e

        enriched_portfolio = []
        for idx, entry in enumerate(portfolio[:max_select]):
            eid = entry.get("experiment_id", entry.get("id", ""))
            full_exp = exp_map.get(eid, {})
            if not full_exp and idx < len(experiments):
                full_exp = experiments[idx]
            enriched_portfolio.append({
                **entry,
                "title": full_exp.get("title", entry.get("title", "")),
                "hypothesis": full_exp.get("hypothesis", entry.get("hypothesis", "")),
                "estimated_effort": full_exp.get("estimated_effort", entry.get("effort", "")),
            })

        return {
            "dossier_id": dossier_id,
            "portfolio": enriched_portfolio,
            "total_expected_gain": data.get("total_expected_gain", 0),
            "budget_utilization": data.get("budget_utilization", 0),
            "uncovered_uncertainties": data.get("uncovered_uncertainties", []),
            "all_candidates": len(experiments),
            "selected": len(enriched_portfolio),
        }

    async def ingest_result(
        self,
        dossier_id: str,
        *,
        experiment_id: str,
        experiment_title: str,
        hypothesis: str,
        protocol: dict,
        results: dict,
        target_claim_ids: list[str] | None = None,
    ) -> dict:
        """Ingest experiment results and propagate into claims/confidence/decisions."""
        from app.clients.llm_client import LLMClient

        claims = await self._get_target_claims(dossier_id, target_claim_ids)
        decision_info = await self._get_decision_context(dossier_id)

        claims_text = "\n".join(
            f"- [{c.get('claim_id', '')[:8]}] {c['text'][:120]}"
            for c in claims[:8]
        ) or "No specific claims targeted"
        decision_text = (
            f"Question: {decision_info.get('decision_question', '')}\n"
            f"Recommended: {decision_info.get('recommended_option', {}).get('title', '')}"
            if decision_info else "No active decision"
        )
        results_text = "\n".join(
            f"- {k}: {v}" for k, v in results.items()
        ) if isinstance(results, dict) else str(results)
        protocol_text = "\n".join(
            f"- {k}: {v}" for k, v in protocol.items()
        ) if isinstance(protocol, dict) else str(protocol)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RESULT_PROMPT.format(
                experiment_title=experiment_title,
                hypothesis=hypothesis,
                protocol=protocol_text,
                results_text=results_text,
                claims_text=claims_text,
                decision_text=decision_text,
            ),
            system=RESULT_SYSTEM,
            max_tokens=1536,
            temperature=0.2,
        )
        interpretation = self._parse_json(raw).get("interpretation", self._parse_json(raw))

        updates_applied = await self._apply_claim_updates(
            interpretation.get("claims_strengthened", []),
            interpretation.get("claims_weakened", []),
        )

        return {
            "dossier_id": dossier_id,
            "experiment_id": experiment_id,
            "outcome": interpretation.get("outcome", "inconclusive"),
            "confidence": interpretation.get("confidence", 0),
            "claims_strengthened": interpretation.get("claims_strengthened", []),
            "claims_weakened": interpretation.get("claims_weakened", []),
            "thesis_impact": interpretation.get("thesis_impact", {}),
            "decision_impact": interpretation.get("decision_impact", {}),
            "new_questions": interpretation.get("new_questions", []),
            "follow_up_needed": interpretation.get("follow_up_needed", False),
            "updates_applied": updates_applied,
        }

    async def replan(
        self,
        dossier_id: str,
        *,
        completed_experiment_ids: list[str] | None = None,
        new_constraints: dict | None = None,
        max_experiments: int = 3,
    ) -> dict:
        """Re-rank follow-up experiments after new results or changed constraints."""
        compiled = await self.compile_experiments(
            dossier_id,
            n_experiments=max_experiments + 2,
            constraints=new_constraints,
        )

        if compiled.get("error"):
            return compiled

        experiments = compiled.get("experiments", [])
        if completed_experiment_ids:
            experiments = [
                e for e in experiments
                if e.get("experiment_id") not in completed_experiment_ids
            ]

        portfolio = await self.compile_portfolio(
            dossier_id,
            experiments=experiments,
            budget=str(new_constraints.get("budget", "medium")) if new_constraints else "medium",
            max_select=max_experiments,
        )

        portfolio["replanned"] = True
        portfolio["excluded_completed"] = completed_experiment_ids or []
        return portfolio

    # ─── Internal helpers ─────────────────────────────────────────────

    async def _gather_unresolved_claims(
        self, dossier_id: str, focus_ids: list[str] | None
    ) -> list[dict]:
        from sqlalchemy import select
        from app.models.claim_ledger import GlobalClaim, ClaimMention

        if focus_ids:
            uuids = [uuid.UUID(c) for c in focus_ids]
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
        else:
            mention_q = await self.db.execute(
                select(ClaimMention.global_claim_id)
                .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
                .distinct().limit(30)
            )
            claim_ids = [r[0] for r in mention_q.all()]
            if not claim_ids:
                return []
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
            )

        claims = list(q.scalars().all())
        unresolved = [
            c for c in claims
            if (c.effective_confidence or c.direct_confidence or 0) < 0.7
        ]
        unresolved.sort(key=lambda c: c.effective_confidence or c.direct_confidence or 0)

        return [
            {
                "claim_id": str(c.id),
                "text": c.canonical_text,
                "confidence": c.effective_confidence or c.direct_confidence or 0,
                "strength": c.evidence_strength_score or 0,
            }
            for c in unresolved[:15]
        ]

    async def _get_rival_theses(self, dossier_id: str, question: str | None) -> list:
        if not question:
            return []
        try:
            from app.services.crux_engine_service import CruxEngineService
            svc = CruxEngineService(self.db)
            result = await svc.analyze_question(
                question, dossier_id=dossier_id,
                n_theses=2, resolve_cruxes=False, budget_papers=0,
            )
            return result.get("theses", [])
        except Exception as e:
            logger.warning("rival_theses_error", error=str(e))
            return []

    async def _get_causal_context(self, dossier_id: str, question: str | None) -> list:
        if not question:
            return []
        try:
            from app.services.causal_model_service import CausalModelService
            svc = CausalModelService(self.db)
            result = await svc.compile_model(
                dossier_id=dossier_id, question=question,
                mode="build", max_claims=10,
            )
            return result.get("nodes", [])[:6]
        except Exception as e:
            logger.warning("causal_context_error", error=str(e))
            return []

    async def _get_decision_context(
        self, dossier_id: str, decision_id: str | None = None
    ) -> dict | None:
        if not decision_id:
            return None
        try:
            from sqlalchemy import select
            from app.models.decision_monitor import DecisionMonitor
            q = await self.db.execute(
                select(DecisionMonitor)
                .where(DecisionMonitor.dossier_id == uuid.UUID(dossier_id))
                .order_by(DecisionMonitor.created_at.desc())
                .limit(1)
            )
            monitor = q.scalar_one_or_none()
            if monitor:
                return {
                    "decision_question": monitor.decision_question,
                    "recommended_option": monitor.recommended_option,
                    "decision_confidence": monitor.decision_confidence,
                }
        except Exception as e:
            logger.warning("decision_context_error", error=str(e))
        return None

    async def _get_crux_claims(
        self, dossier_id: str, crux_ids: list[str] | None
    ) -> list[dict]:
        if crux_ids:
            from sqlalchemy import select
            from app.models.claim_ledger import GlobalClaim
            uuids = [uuid.UUID(c) for c in crux_ids]
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
            claims = list(q.scalars().all())
            return [
                {"claim_id": str(c.id), "text": c.canonical_text}
                for c in claims
            ]
        return []

    async def _gather_evidence_summary(self, dossier_id: str) -> list[dict]:
        from sqlalchemy import select
        from app.models.claim_ledger import GlobalClaim, ClaimMention

        mention_q = await self.db.execute(
            select(ClaimMention.global_claim_id)
            .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
            .distinct().limit(20)
        )
        claim_ids = [r[0] for r in mention_q.all()]
        if not claim_ids:
            return []

        q = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        claims = list(q.scalars().all())
        claims.sort(key=lambda c: c.evidence_strength_score or 0, reverse=True)

        return [
            {
                "claim_id": str(c.id),
                "text": c.canonical_text,
                "strength": c.evidence_strength_score or 0,
            }
            for c in claims[:10]
        ]

    async def _get_target_claims(
        self, dossier_id: str, claim_ids: list[str] | None
    ) -> list[dict]:
        if claim_ids:
            from sqlalchemy import select
            from app.models.claim_ledger import GlobalClaim
            uuids = [uuid.UUID(c) for c in claim_ids]
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
            claims = list(q.scalars().all())
            return [
                {"claim_id": str(c.id), "text": c.canonical_text}
                for c in claims
            ]
        return await self._gather_evidence_summary(dossier_id)

    async def _apply_claim_updates(
        self, strengthened: list, weakened: list
    ) -> int:
        """Apply confidence updates to claims based on experiment results."""
        updates = 0
        try:
            from sqlalchemy import select
            from app.models.claim_ledger import GlobalClaim

            for entry in strengthened:
                cid = entry.get("claim_id")
                delta = entry.get("delta", 0.1)
                if not cid:
                    continue
                try:
                    q = await self.db.execute(
                        select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(cid))
                    )
                    claim = q.scalar_one_or_none()
                    if claim:
                        current = claim.effective_confidence or claim.direct_confidence or 0
                        claim.direct_confidence = min(1.0, current + delta)
                        claim.support_count = (claim.support_count or 0) + 1
                        updates += 1
                except Exception:
                    continue

            for entry in weakened:
                cid = entry.get("claim_id")
                delta = entry.get("delta", 0.1)
                if not cid:
                    continue
                try:
                    q = await self.db.execute(
                        select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(cid))
                    )
                    claim = q.scalar_one_or_none()
                    if claim:
                        current = claim.effective_confidence or claim.direct_confidence or 0
                        claim.direct_confidence = max(0.0, current - delta)
                        claim.contradict_count = (claim.contradict_count or 0) + 1
                        updates += 1
                except Exception:
                    continue

            if updates:
                await self.db.commit()
        except Exception as e:
            logger.warning("claim_update_error", error=str(e))
        return updates

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)(?:\n?```|$)", text, re.DOTALL)
        if fence:
            try:
                return json.loads(fence.group(1).strip())
            except json.JSONDecodeError:
                repaired = self._repair_json(fence.group(1).strip())
                if repaired:
                    return repaired
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        return {}

    def _repair_json(self, text: str) -> dict | None:
        import json
        text = text.rstrip().rstrip(",")
        stack = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()
        if in_string:
            text += '"'
        text = text.rstrip().rstrip(",")
        text += ''.join(reversed(stack))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
