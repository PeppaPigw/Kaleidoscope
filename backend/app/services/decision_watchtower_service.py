"""DecisionWatchtowerService — Living decision monitoring.

Keeps compiled decisions current by tracking change-my-mind triggers,
watching for new evidence, and re-evaluating recommendations when
assumptions break or boundary conditions are crossed.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision_monitor import DecisionMonitor, DecisionMonitorRun

logger = structlog.get_logger(__name__)

DRIFT_SYSTEM = """You are a decision drift evaluator. Given a decision's assumptions, triggers, and new evidence, determine whether the original recommendation still holds.

Output JSON only:
{"drift_score": 0.0-1.0, "triggers_fired": ["trigger text"], "recommendation_holds": true/false, "reason": "one sentence", "new_evidence_summary": "one sentence or null"}"""

DRIFT_PROMPT = """Original decision: {question}
Recommended option: {recommended_option}
Original confidence: {confidence}

Assumptions (must hold for recommendation to be valid):
{assumptions}

Boundary conditions (recommendation breaks if crossed):
{boundary_conditions}

Change-my-mind triggers:
{triggers}

New evidence since last check:
{new_evidence}

Evaluate drift. Return ONLY valid JSON."""


class DecisionWatchtowerService:
    """Monitors compiled decisions and re-evaluates when triggers fire."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_monitor(
        self,
        decision_record: dict,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Create a live monitor from a compiled decision record."""
        did = dossier_id or decision_record.get("dossier_id")
        if not did:
            return {"error": "dossier_id is required"}

        decision_id = decision_record.get("decision_id", str(uuid.uuid4()))
        question = decision_record.get("decision_question", "")
        recommended = decision_record.get("recommended_option", {})
        triggers = decision_record.get("change_my_mind_triggers", [])
        assumptions = decision_record.get("assumptions", [])
        boundary_conditions = decision_record.get("boundary_conditions", [])
        confidence = decision_record.get("decision_confidence", 0)
        fragility = decision_record.get("fragility", {}).get("score", 0)

        monitor = DecisionMonitor(
            dossier_id=uuid.UUID(did),
            decision_id=decision_id,
            decision_question=question,
            recommended_option=recommended,
            triggers=triggers,
            assumptions=assumptions,
            boundary_conditions=boundary_conditions,
            decision_confidence=confidence,
            fragility_score=fragility,
            status="active",
            drift_score=0.0,
            version=1,
            recommendation_changed=False,
        )
        self.db.add(monitor)
        await self.db.commit()

        return {
            "monitor_id": str(monitor.id),
            "decision_id": decision_id,
            "decision_question": question,
            "status": "active",
            "triggers_count": len(triggers),
            "assumptions_count": len(assumptions),
            "fragility_score": fragility,
        }

    async def list_monitors(
        self,
        dossier_id: str | None = None,
        status: str | None = None,
    ) -> dict:
        """List active decision monitors."""
        q = select(DecisionMonitor)
        if dossier_id:
            q = q.where(DecisionMonitor.dossier_id == uuid.UUID(dossier_id))
        if status:
            q = q.where(DecisionMonitor.status == status)
        q = q.order_by(DecisionMonitor.created_at.desc()).limit(50)

        result = await self.db.execute(q)
        monitors = list(result.scalars().all())

        return {
            "monitors": [
                {
                    "monitor_id": str(m.id),
                    "decision_id": m.decision_id,
                    "decision_question": m.decision_question,
                    "status": m.status,
                    "decision_confidence": m.decision_confidence,
                    "drift_score": m.drift_score,
                    "version": m.version,
                    "recommendation_changed": m.recommendation_changed,
                    "last_check_at": str(m.last_check_at) if m.last_check_at else None,
                }
                for m in monitors
            ],
            "count": len(monitors),
        }

    async def get_status(self, monitor_id: str) -> dict:
        """Get detailed status of a decision monitor."""
        monitor = await self._get_monitor(monitor_id)
        if not monitor:
            return {"error": f"Monitor {monitor_id} not found"}

        runs_q = await self.db.execute(
            select(DecisionMonitorRun)
            .where(DecisionMonitorRun.monitor_id == monitor.id)
            .order_by(DecisionMonitorRun.started_at.desc())
            .limit(5)
        )
        recent_runs = list(runs_q.scalars().all())

        return {
            "monitor_id": str(monitor.id),
            "decision_id": monitor.decision_id,
            "decision_question": monitor.decision_question,
            "recommended_option": monitor.recommended_option,
            "status": monitor.status,
            "decision_confidence": monitor.decision_confidence,
            "drift_score": monitor.drift_score,
            "fragility_score": monitor.fragility_score,
            "version": monitor.version,
            "recommendation_changed": monitor.recommendation_changed,
            "triggers": monitor.triggers,
            "assumptions": monitor.assumptions,
            "boundary_conditions": monitor.boundary_conditions,
            "last_check_at": str(monitor.last_check_at) if monitor.last_check_at else None,
            "recent_runs": [
                {
                    "run_id": str(r.id),
                    "started_at": str(r.started_at),
                    "triggers_fired": r.triggers_fired,
                    "new_evidence_found": r.new_evidence_found,
                    "drift_delta": r.drift_delta,
                    "recommendation_changed": r.recommendation_changed,
                }
                for r in recent_runs
            ],
        }

    async def run_check(
        self,
        monitor_id: str,
        *,
        lookback_days: int = 30,
        budget_papers: int = 5,
    ) -> dict:
        """Run one monitoring cycle: check triggers against new evidence."""
        monitor = await self._get_monitor(monitor_id)
        if not monitor:
            return {"error": f"Monitor {monitor_id} not found"}

        run = DecisionMonitorRun(
            monitor_id=monitor.id,
            started_at=datetime.now(timezone.utc),
            triggers_checked=0,
            triggers_fired=0,
            new_evidence_found=0,
            drift_delta=0.0,
            recommendation_changed=False,
        )
        self.db.add(run)

        new_evidence = await self._gather_new_evidence(
            str(monitor.dossier_id), monitor.decision_question,
            lookback_days=lookback_days, budget_papers=budget_papers,
        )

        drift_result = await self._evaluate_drift(monitor, new_evidence)

        run.triggers_checked = len(monitor.triggers or [])
        run.triggers_fired = len(drift_result.get("triggers_fired", []))
        run.new_evidence_found = len(new_evidence)
        run.drift_delta = drift_result.get("drift_score", 0) - monitor.drift_score
        run.recommendation_changed = not drift_result.get("recommendation_holds", True)
        run.finished_at = datetime.now(timezone.utc)
        run.summary = drift_result

        old_drift = monitor.drift_score
        monitor.drift_score = drift_result.get("drift_score", old_drift)
        monitor.last_check_at = datetime.now(timezone.utc)

        if run.recommendation_changed:
            run.previous_option = monitor.recommended_option
            monitor.recommendation_changed = True

        await self.db.commit()

        return {
            "monitor_id": str(monitor.id),
            "run_id": str(run.id),
            "triggers_checked": run.triggers_checked,
            "triggers_fired": run.triggers_fired,
            "new_evidence_found": run.new_evidence_found,
            "drift_score": monitor.drift_score,
            "drift_delta": run.drift_delta,
            "recommendation_holds": drift_result.get("recommendation_holds", True),
            "reason": drift_result.get("reason", ""),
            "fired_triggers": drift_result.get("triggers_fired", []),
        }

    async def re_evaluate(self, monitor_id: str) -> dict:
        """Recompile the decision after a trigger fires or on demand."""
        monitor = await self._get_monitor(monitor_id)
        if not monitor:
            return {"error": f"Monitor {monitor_id} not found"}

        from app.services.decision_compiler_service import DecisionCompilerService
        compiler = DecisionCompilerService(self.db)

        new_decision = await compiler.compile_decision(
            str(monitor.dossier_id),
            decision_question=monitor.decision_question,
            auto_monitor=False,
        )

        if new_decision.get("error"):
            return {"error": new_decision["error"], "monitor_id": str(monitor.id)}

        old_option = monitor.recommended_option
        new_option = new_decision.get("recommended_option", {})
        changed = (
            old_option.get("id") != new_option.get("id")
            if old_option and new_option else True
        )

        monitor.recommended_option = new_option
        monitor.decision_confidence = new_decision.get("decision_confidence", 0)
        monitor.assumptions = new_decision.get("assumptions", [])
        monitor.boundary_conditions = new_decision.get("boundary_conditions", [])
        monitor.triggers = new_decision.get("change_my_mind_triggers", [])
        monitor.fragility_score = new_decision.get("fragility", {}).get("score", 0)
        monitor.version += 1
        monitor.recommendation_changed = changed
        monitor.drift_score = 0.0
        monitor.last_check_at = datetime.now(timezone.utc)

        await self.db.commit()

        return {
            "monitor_id": str(monitor.id),
            "version": monitor.version,
            "recommendation_changed": changed,
            "previous_option": old_option,
            "new_option": new_option,
            "new_confidence": monitor.decision_confidence,
            "new_fragility": monitor.fragility_score,
            "new_decision": new_decision,
        }

    async def get_digest(self, monitor_id: str, *, last_n_runs: int = 5) -> dict:
        """Summarize what changed since the last run."""
        monitor = await self._get_monitor(monitor_id)
        if not monitor:
            return {"error": f"Monitor {monitor_id} not found"}

        runs_q = await self.db.execute(
            select(DecisionMonitorRun)
            .where(DecisionMonitorRun.monitor_id == monitor.id)
            .order_by(DecisionMonitorRun.started_at.desc())
            .limit(last_n_runs)
        )
        runs = list(runs_q.scalars().all())

        total_triggers_fired = sum(r.triggers_fired for r in runs)
        total_evidence = sum(r.new_evidence_found for r in runs)
        any_changed = any(r.recommendation_changed for r in runs)
        max_drift = max((r.drift_delta for r in runs), default=0)

        stability = "stable" if not any_changed and monitor.drift_score < 0.3 else (
            "drifting" if monitor.drift_score < 0.6 else "unstable"
        )

        return {
            "monitor_id": str(monitor.id),
            "decision_question": monitor.decision_question,
            "current_recommendation": monitor.recommended_option,
            "version": monitor.version,
            "stability": stability,
            "drift_score": monitor.drift_score,
            "runs_analyzed": len(runs),
            "total_triggers_fired": total_triggers_fired,
            "total_new_evidence": total_evidence,
            "recommendation_ever_changed": monitor.recommendation_changed,
            "max_drift_delta": max_drift,
            "assessment": (
                f"Decision is {stability}. "
                f"{total_triggers_fired} triggers fired across {len(runs)} checks. "
                f"{'Recommendation has changed.' if any_changed else 'Original recommendation holds.'}"
            ),
        }

    async def _get_monitor(self, monitor_id: str) -> DecisionMonitor | None:
        result = await self.db.execute(
            select(DecisionMonitor).where(DecisionMonitor.id == uuid.UUID(monitor_id))
        )
        return result.scalar_one_or_none()

    async def _gather_new_evidence(
        self, dossier_id: str, question: str,
        lookback_days: int = 30, budget_papers: int = 5,
    ) -> list[dict]:
        """Find new evidence relevant to the decision question."""
        try:
            from app.services.search.vector_search import VectorSearchService
            search_svc = VectorSearchService()
            results = search_svc.search(query=question, top_k=budget_papers)
            return [
                {
                    "title": p.get("payload", {}).get("title", ""),
                    "abstract": p.get("payload", {}).get("abstract", "")[:200],
                    "year": p.get("payload", {}).get("year"),
                    "relevance": p.get("score", 0),
                }
                for p in results[:budget_papers]
            ]
        except Exception as e:
            logger.warning("evidence_gather_error", error=str(e))
            return []

    async def _evaluate_drift(self, monitor: DecisionMonitor, new_evidence: list) -> dict:
        """Use LLM to evaluate whether triggers have fired."""
        if not new_evidence and not monitor.triggers:
            return {"drift_score": 0.0, "triggers_fired": [], "recommendation_holds": True, "reason": "No new evidence or triggers to evaluate"}

        from app.clients.llm_client import LLMClient

        triggers_text = "\n".join(
            f"- {t.get('trigger', t) if isinstance(t, dict) else t}"
            for t in (monitor.triggers or [])
        ) or "None"
        assumptions_text = "\n".join(
            f"- {a}" for a in (monitor.assumptions or [])
        ) or "None"
        boundary_text = "\n".join(
            f"- {b}" for b in (monitor.boundary_conditions or [])
        ) or "None"
        evidence_text = "\n".join(
            f"- {e['title']}: {e.get('abstract', '')[:100]}"
            for e in new_evidence[:8]
        ) or "No new evidence found"

        recommended = monitor.recommended_option or {}
        option_text = f"{recommended.get('title', 'Unknown')} — {recommended.get('description', '')}"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DRIFT_PROMPT.format(
                question=monitor.decision_question,
                recommended_option=option_text,
                confidence=monitor.decision_confidence,
                assumptions=assumptions_text,
                boundary_conditions=boundary_text,
                triggers=triggers_text,
                new_evidence=evidence_text,
            ),
            system=DRIFT_SYSTEM,
            max_tokens=1024,
            temperature=0.2,
        )
        return self._parse_json(raw)

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
                pass
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        return {"drift_score": 0.0, "triggers_fired": [], "recommendation_holds": True, "reason": "Could not parse drift evaluation"}

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
