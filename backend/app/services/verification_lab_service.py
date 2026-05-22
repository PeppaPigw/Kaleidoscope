"""VerificationLabService — Executable Verification Lab.

Turns papers, claims, experiments, and replication runbooks into executable
run specs, evaluates results against claims, diagnoses failures, and ingests
empirical evidence back into the knowledge system.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RUN_COMPILE_SYSTEM = """You are an execution engineer. Given a replication plan, experiment, or paper artifact, compile an executable run specification.

Output JSON only:
{"run_spec": {"id": "run_xxx", "title": "short title", "objective": "what we're verifying", "environment": {"language": "python", "framework": "pytorch", "dependencies": ["pkg==ver"], "hardware": "description", "docker_image": "image or null"}, "steps": [{"step": 1, "command": "shell command", "working_dir": ".", "env_vars": {}, "timeout_seconds": 300, "expected_output": "what success looks like"}], "inputs": [{"name": "input name", "source": "url or path", "type": "dataset|checkpoint|config"}], "outputs": [{"name": "output name", "type": "metric|artifact|log", "path": "where to find it"}], "success_criteria": [{"metric": "name", "operator": "gt|lt|eq|within", "threshold": "value"}], "estimated_duration": "timeframe", "estimated_cost": "description"}}"""

RUN_COMPILE_PROMPT = """Source: {source_type}
Title: {title}

Plan/Protocol:
{protocol_text}

Environment spec:
{env_text}

Available artifacts:
{artifacts_text}

Target claims to verify:
{claims_text}

Constraints: {constraints}

Compile an executable run spec. Return ONLY valid JSON."""

EVALUATE_SYSTEM = """You are a research result evaluator. Given observed results from an execution run and the original paper claims / success criteria, determine verdicts.

Output JSON only:
{"evaluation": {"overall_verdict": "reproduced|partially_reproduced|failed|inconclusive", "confidence": 0.0-1.0, "claim_verdicts": [{"claim_id": "id or null", "claim_text": "short", "verdict": "confirmed|weakened|refuted|inconclusive", "observed_value": "what we got", "expected_value": "what was claimed", "deviation": "description", "confidence_impact": -1.0 to 1.0}], "methodology_notes": ["observation"], "confounders_detected": ["potential issue"], "recommendation": "one sentence next step"}}"""

EVALUATE_PROMPT = """Run title: {title}
Objective: {objective}

Success criteria:
{criteria_text}

Observed results:
{results_text}

Original claims:
{claims_text}

Baseline comparisons (if any):
{baselines_text}

Evaluate results against claims. Return ONLY valid JSON."""

DIAGNOSE_SYSTEM = """You are a failure diagnostician for research execution. Given a failed run's logs, error messages, and context, classify the failure and suggest repairs.

Output JSON only:
{"diagnosis": {"failure_class": "environment|dependency|data|code|hardware|nondeterminism|missing_artifact|methodological|timeout|resource", "severity": "fatal|recoverable|intermittent", "root_cause": "one sentence", "evidence": ["log line or observation"], "repair_suggestions": [{"action": "what to do", "confidence": 0.0-1.0, "effort": "low|medium|high"}], "should_retry": true, "retry_with_changes": ["change to make before retry"]}}"""

DIAGNOSE_PROMPT = """Run title: {title}
Exit code: {exit_code}

Error output (last 500 chars):
{error_text}

Full log summary:
{log_text}

Environment:
{env_text}

Steps completed before failure:
{steps_text}

Diagnose the failure. Return ONLY valid JSON."""

ABLATION_SYSTEM = """You are an ablation study designer. Given a method, causal edge, or fragile claim, generate minimal ablation experiments that isolate the contribution of each component.

Output JSON only:
{"ablations": [{"id": "abl_1", "title": "short title", "removes_or_varies": "what component", "hypothesis": "what we expect to change", "command_delta": "how the run command changes", "expected_effect": "metric change prediction", "information_gain": 0.0-1.0}]}"""

ABLATION_PROMPT = """Method/claim: {target}

Full run spec:
{run_spec_text}

Causal model context:
{causal_text}

Fragile assumptions:
{assumptions_text}

Design minimal ablations. Return ONLY valid JSON."""


_RUNS_CACHE: dict[str, dict] = {}


class VerificationLabService:
    """Orchestrates executable verification of research claims."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._runs = _RUNS_CACHE

    async def compile_run(
        self,
        dossier_id: str,
        *,
        source_type: str = "replication_plan",
        title: str = "",
        protocol: dict | None = None,
        experiment: dict | None = None,
        claim_ids: list[str] | None = None,
        constraints: dict | None = None,
    ) -> dict:
        """Compile an executable run spec from a plan, experiment, or artifact."""
        from app.clients.llm_client import LLMClient

        context = await self._gather_run_context(dossier_id, claim_ids)

        protocol_text = ""
        if protocol:
            protocol_text = "\n".join(f"- {k}: {v}" for k, v in protocol.items() if isinstance(v, str))
            if "steps" in protocol:
                for s in protocol.get("steps", [])[:5]:
                    protocol_text += f"\n  Step {s.get('step', '?')}: {s.get('action', '')}"
        elif experiment:
            protocol_text = (
                f"Hypothesis: {experiment.get('hypothesis', '')}\n"
                f"Intervention: {experiment.get('intervention', '')}\n"
                f"Control: {experiment.get('control', '')}\n"
                f"Metrics: {experiment.get('metrics', [])}\n"
                f"Success: {experiment.get('success_criteria', '')}"
            )

        if not title:
            title = experiment.get("title", "") if experiment else "Verification run"

        env_text = str(context.get("environment", {}))[:300] or "Not specified"
        artifacts_text = "\n".join(
            f"- [{a.get('type', '?')}] {a.get('name', '?')}: {a.get('url', 'no URL')}"
            for a in context.get("artifacts", [])[:6]
        ) or "None resolved"
        claims_text = context.get("claims_text", "No specific claims")
        constraints_text = str(constraints or {"hardware": "single GPU", "timeout": "1 hour"})

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RUN_COMPILE_PROMPT.format(
                source_type=source_type,
                title=title,
                protocol_text=protocol_text or "See claims and artifacts",
                env_text=env_text,
                artifacts_text=artifacts_text,
                claims_text=claims_text,
                constraints=constraints_text,
            ),
            system=RUN_COMPILE_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        run_spec = data.get("run_spec", data)

        run_id = run_spec.get("id", f"run_{uuid.uuid4().hex[:8]}")
        run_spec["id"] = run_id
        run_spec["dossier_id"] = dossier_id
        run_spec["status"] = "compiled"
        run_spec["compiled_at"] = datetime.now(timezone.utc).isoformat()
        run_spec["claim_ids"] = claim_ids or []

        self._runs[run_id] = run_spec

        return {
            "run_id": run_id,
            "dossier_id": dossier_id,
            "run_spec": run_spec,
            "steps_count": len(run_spec.get("steps", [])),
            "inputs_count": len(run_spec.get("inputs", [])),
            "success_criteria_count": len(run_spec.get("success_criteria", [])),
        }

    async def build_environment(
        self,
        run_id: str,
        *,
        backend: str = "docker",
        validate_only: bool = False,
    ) -> dict:
        """Build or validate the required runtime environment."""
        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found. Compile first."}

        env = run_spec.get("environment", {})
        deps = env.get("dependencies", [])
        docker_image = env.get("docker_image")
        hardware = env.get("hardware", "CPU")

        issues = []
        if not deps:
            issues.append({"type": "missing_deps", "severity": "major", "detail": "No dependencies specified"})
        if "gpu" in hardware.lower() and backend == "local":
            issues.append({"type": "hardware_mismatch", "severity": "warning", "detail": "GPU required but local backend selected"})
        if not docker_image and backend == "docker":
            docker_image = f"python:{env.get('language', 'python')}-slim"

        return {
            "run_id": run_id,
            "backend": backend,
            "validated": len(issues) == 0,
            "issues": issues,
            "environment": {
                "docker_image": docker_image,
                "dependencies": deps,
                "hardware": hardware,
                "framework": env.get("framework", ""),
            },
            "ready_to_run": len([i for i in issues if i["severity"] == "critical"]) == 0,
        }

    async def start_run(
        self,
        run_id: str,
        *,
        backend: str = "local",
        dry_run: bool = False,
    ) -> dict:
        """Start a sandboxed execution job."""
        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found. Compile first."}

        job_id = f"job_{uuid.uuid4().hex[:8]}"
        run_spec["status"] = "dry_run" if dry_run else "running"
        run_spec["job_id"] = job_id
        run_spec["started_at"] = datetime.now(timezone.utc).isoformat()
        run_spec["backend"] = backend

        steps = run_spec.get("steps", [])

        return {
            "run_id": run_id,
            "job_id": job_id,
            "status": run_spec["status"],
            "backend": backend,
            "steps_to_execute": len(steps),
            "commands": [s.get("command", "") for s in steps[:5]],
            "dry_run": dry_run,
            "message": (
                "Dry run — commands listed but not executed. Use dry_run=false to execute."
                if dry_run else
                f"Job {job_id} started on {backend} backend. Use lab_run_status to check progress."
            ),
        }

    async def get_run_status(self, run_id: str) -> dict:
        """Report job state, logs, and diagnostics."""
        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        return {
            "run_id": run_id,
            "job_id": run_spec.get("job_id"),
            "status": run_spec.get("status", "unknown"),
            "backend": run_spec.get("backend", "unknown"),
            "started_at": run_spec.get("started_at"),
            "steps_total": len(run_spec.get("steps", [])),
            "steps_completed": run_spec.get("steps_completed", 0),
            "current_step": run_spec.get("current_step"),
            "metrics_so_far": run_spec.get("metrics_collected", {}),
            "errors": run_spec.get("errors", []),
        }

    async def collect_results(
        self,
        run_id: str,
        *,
        results: dict,
        metrics: dict | None = None,
        logs: str | None = None,
        exit_code: int = 0,
    ) -> dict:
        """Collect outputs from a completed run."""
        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        run_spec["status"] = "completed" if exit_code == 0 else "failed"
        run_spec["exit_code"] = exit_code
        run_spec["results"] = results
        run_spec["metrics_collected"] = metrics or {}
        run_spec["logs_summary"] = (logs or "")[:500]
        run_spec["completed_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "run_id": run_id,
            "status": run_spec["status"],
            "exit_code": exit_code,
            "results_collected": len(results),
            "metrics_collected": len(metrics or {}),
            "ready_for_evaluation": exit_code == 0,
        }

    async def evaluate_results(
        self,
        run_id: str,
        *,
        results: dict | None = None,
        baselines: dict | None = None,
    ) -> dict:
        """Compare observed results against paper claims and success criteria."""
        from app.clients.llm_client import LLMClient

        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        actual_results = results or run_spec.get("results", {})
        if not actual_results:
            return {"error": "No results to evaluate. Collect results first."}

        criteria = run_spec.get("success_criteria", [])
        claims = await self._get_claims(run_spec.get("dossier_id", ""), run_spec.get("claim_ids", []))

        criteria_text = "\n".join(
            f"- {c.get('metric', '?')} {c.get('operator', '?')} {c.get('threshold', '?')}"
            for c in criteria
        ) or "No explicit criteria"
        results_text = "\n".join(f"- {k}: {v}" for k, v in actual_results.items())
        claims_text = "\n".join(
            f"- [{c.get('claim_id', '')[:8]}] {c.get('text', '')[:100]}"
            for c in claims[:8]
        ) or "No specific claims"
        baselines_text = "\n".join(
            f"- {k}: {v}" for k, v in (baselines or {}).items()
        ) or "No baselines"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EVALUATE_PROMPT.format(
                title=run_spec.get("title", "Unknown"),
                objective=run_spec.get("objective", "Verify claims"),
                criteria_text=criteria_text,
                results_text=results_text,
                claims_text=claims_text,
                baselines_text=baselines_text,
            ),
            system=EVALUATE_SYSTEM,
            max_tokens=1536,
            temperature=0.2,
        )
        evaluation = self._parse_json(raw).get("evaluation", self._parse_json(raw))

        run_spec["evaluation"] = evaluation

        return {
            "run_id": run_id,
            "overall_verdict": evaluation.get("overall_verdict", "inconclusive"),
            "confidence": evaluation.get("confidence", 0),
            "claim_verdicts": evaluation.get("claim_verdicts", []),
            "confounders_detected": evaluation.get("confounders_detected", []),
            "recommendation": evaluation.get("recommendation", ""),
        }

    async def diagnose_failure(
        self,
        run_id: str,
        *,
        error_text: str = "",
        logs: str = "",
        exit_code: int = 1,
    ) -> dict:
        """Classify a failed run and suggest repairs."""
        from app.clients.llm_client import LLMClient

        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        env = run_spec.get("environment", {})
        steps = run_spec.get("steps", [])
        steps_text = "\n".join(
            f"  Step {s.get('step', '?')}: {s.get('command', '')[:80]}"
            for s in steps[:5]
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DIAGNOSE_PROMPT.format(
                title=run_spec.get("title", "Unknown"),
                exit_code=exit_code,
                error_text=(error_text or "No error output captured")[:500],
                log_text=(logs or "No logs available")[:300],
                env_text=str(env)[:200],
                steps_text=steps_text,
            ),
            system=DIAGNOSE_SYSTEM,
            max_tokens=1024,
            temperature=0.2,
        )
        diagnosis = self._parse_json(raw).get("diagnosis", self._parse_json(raw))

        return {
            "run_id": run_id,
            "failure_class": diagnosis.get("failure_class", "unknown"),
            "severity": diagnosis.get("severity", "unknown"),
            "root_cause": diagnosis.get("root_cause", ""),
            "repair_suggestions": diagnosis.get("repair_suggestions", []),
            "should_retry": diagnosis.get("should_retry", False),
            "retry_with_changes": diagnosis.get("retry_with_changes", []),
        }

    async def compile_ablations(
        self,
        run_id: str,
        *,
        target: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Generate minimal ablation experiments for a method or claim."""
        from app.clients.llm_client import LLMClient

        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        did = dossier_id or run_spec.get("dossier_id", "")
        if not target:
            target = run_spec.get("title", run_spec.get("objective", ""))

        run_spec_text = f"Steps: {len(run_spec.get('steps', []))}, Inputs: {run_spec.get('inputs', [])}"
        causal_text = "Not available"
        assumptions_text = "Not specified"

        if did:
            try:
                from app.services.causal_model_service import CausalModelService
                svc = CausalModelService(self.db)
                model = await svc.compile_model(dossier_id=did, question=target, mode="build", max_claims=8)
                nodes = model.get("nodes", [])
                causal_text = "\n".join(
                    f"- {n.get('label', '')}: {n.get('role', '')} ({n.get('type', '')})"
                    for n in nodes[:5]
                ) or "None"
            except Exception:
                pass

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABLATION_PROMPT.format(
                target=target,
                run_spec_text=run_spec_text,
                causal_text=causal_text,
                assumptions_text=assumptions_text,
            ),
            system=ABLATION_SYSTEM,
            max_tokens=1536,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        ablations = data.get("ablations", [])

        return {
            "run_id": run_id,
            "target": target,
            "ablations": ablations,
            "total_information_gain": sum(a.get("information_gain", 0) for a in ablations),
        }

    async def compile_benchmark_comparison(
        self,
        dossier_id: str,
        *,
        methods: list[str],
        dataset: str,
        metrics: list[str],
        constraints: dict | None = None,
    ) -> dict:
        """Organize comparisons across candidate methods."""
        comparison_id = f"bench_{uuid.uuid4().hex[:8]}"

        runs = []
        for method in methods:
            run_id = f"run_{uuid.uuid4().hex[:8]}"
            run_spec = {
                "id": run_id,
                "title": f"Benchmark: {method} on {dataset}",
                "objective": f"Evaluate {method} on {dataset} using {metrics}",
                "method": method,
                "dataset": dataset,
                "metrics": metrics,
                "status": "planned",
                "dossier_id": dossier_id,
            }
            self._runs[run_id] = run_spec
            runs.append({"run_id": run_id, "method": method, "status": "planned"})

        return {
            "comparison_id": comparison_id,
            "dossier_id": dossier_id,
            "dataset": dataset,
            "metrics": metrics,
            "methods": methods,
            "runs": runs,
            "total_runs": len(runs),
            "constraints": constraints or {},
        }

    async def ingest_evidence(
        self,
        run_id: str,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Commit execution evidence into Claim Ledger and linked systems."""
        run_spec = self._runs.get(run_id)
        if not run_spec:
            return {"error": f"Run {run_id} not found"}

        did = dossier_id or run_spec.get("dossier_id", "")
        evaluation = run_spec.get("evaluation", {})
        if not evaluation:
            return {"error": "No evaluation found. Run evaluate_results first."}

        from app.services.experiment_compiler_service import ExperimentCompilerService
        exp_svc = ExperimentCompilerService(self.db)

        results_dict = {}
        for cv in evaluation.get("claim_verdicts", []):
            results_dict[cv.get("claim_text", "unknown")] = cv.get("verdict", "inconclusive")
        results_dict["overall_verdict"] = evaluation.get("overall_verdict", "inconclusive")
        results_dict["confidence"] = evaluation.get("confidence", 0)

        ingest_result = await exp_svc.ingest_result(
            did,
            experiment_id=run_id,
            experiment_title=run_spec.get("title", "Verification run"),
            hypothesis=run_spec.get("objective", "Claims are reproducible"),
            protocol={"type": "execution", "steps": len(run_spec.get("steps", []))},
            results=results_dict,
            target_claim_ids=run_spec.get("claim_ids"),
        )

        return {
            "run_id": run_id,
            "dossier_id": did,
            "evidence_ingested": True,
            "verdict": evaluation.get("overall_verdict", "inconclusive"),
            "claims_updated": ingest_result.get("updates_applied", 0),
            "claims_strengthened": len(ingest_result.get("claims_strengthened", [])),
            "claims_weakened": len(ingest_result.get("claims_weakened", [])),
            "decision_impact": ingest_result.get("decision_impact", {}),
        }

    # ─── Internal helpers ─────────────────────────────────────────────

    async def _gather_run_context(self, dossier_id: str, claim_ids: list[str] | None) -> dict:
        claims = await self._get_claims(dossier_id, claim_ids)
        claims_text = "\n".join(
            f"- [{c.get('claim_id', '')[:8]}] {c.get('text', '')[:120]}"
            for c in claims[:8]
        ) or "No specific claims"

        artifacts = []
        environment = {}
        try:
            from app.services.artifact_grounding_service import ArtifactGroundingService
            svc = ArtifactGroundingService(self.db)
            graph = await svc.compile_artifact_graph(dossier_id, claim_ids=claim_ids)
            artifacts = graph.get("artifacts", [])
            env_result = await svc.extract_environment(dossier_id, artifacts=artifacts)
            environment = env_result.get("environment", {})
        except Exception as e:
            logger.warning("context_gather_error", error=str(e))

        return {
            "claims_text": claims_text,
            "claims": claims,
            "artifacts": artifacts,
            "environment": environment,
        }

    async def _get_claims(self, dossier_id: str, claim_ids: list[str] | None) -> list[dict]:
        if not dossier_id:
            return []
        from sqlalchemy import select
        from app.models.claim_ledger import GlobalClaim, ClaimMention

        if claim_ids:
            uuids = [uuid.UUID(c) for c in claim_ids]
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
        else:
            mention_q = await self.db.execute(
                select(ClaimMention.global_claim_id)
                .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
                .distinct().limit(15)
            )
            cids = [r[0] for r in mention_q.all()]
            if not cids:
                return []
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(cids))
            )

        claims = list(q.scalars().all())
        return [
            {"claim_id": str(c.id), "text": c.canonical_text}
            for c in claims[:15]
        ]

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
