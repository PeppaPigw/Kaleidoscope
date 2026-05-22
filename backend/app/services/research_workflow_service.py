"""ResearchWorkflowService — Automated Multi-Engine Pipeline Execution.

Executes multi-step research pipelines automatically. Unlike meta_plan_pipeline
which only plans, this service actually runs the steps sequentially, feeding
outputs between engines to produce comprehensive research intelligence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WORKFLOW_TEMPLATES = {
    "deep_analysis": [
        {"engine": "hypothesis_generate", "input_key": "question", "output_key": "hypotheses"},
        {"engine": "argument_map", "input_key": "argument", "source": "hypotheses.0.hypothesis", "output_key": "argument_structure"},
        {"engine": "replication_predict", "input_key": "finding", "source": "hypotheses.0.hypothesis", "output_key": "replication"},
        {"engine": "insight_crystallize", "input_key": "question", "extra_input": {"intelligence": "collect_all"}, "output_key": "crystal"},
    ],
    "critical_review": [
        {"engine": "argument_map", "input_key": "argument", "output_key": "structure"},
        {"engine": "argument_detect_fallacies", "input_key": "text", "output_key": "fallacies"},
        {"engine": "blind_spot_detect", "input_key": "question", "output_key": "blind_spots"},
        {"engine": "contradiction_detect", "input_key": "claims", "source": "structure.premises", "output_key": "contradictions"},
    ],
    "impact_assessment": [
        {"engine": "quality_score", "input_key": "topic", "output_key": "quality"},
        {"engine": "replication_predict", "input_key": "finding", "output_key": "replication"},
        {"engine": "impact_forecast", "input_key": "finding", "output_key": "impact"},
        {"engine": "temporal_momentum", "input_key": "topic", "output_key": "momentum"},
    ],
    "exploration": [
        {"engine": "hypothesis_generate", "input_key": "question", "output_key": "hypotheses"},
        {"engine": "serendipity_bisociate", "input_key": "concept_a", "output_key": "serendipity"},
        {"engine": "graph_find_bridges", "input_key": "source", "output_key": "bridges"},
        {"engine": "scenario_generate", "input_key": "situation", "output_key": "scenarios"},
    ],
    "full_investigation": [
        {"engine": "hypothesis_generate", "input_key": "question", "output_key": "hypotheses"},
        {"engine": "methodology_recommend", "input_key": "question", "output_key": "methodology"},
        {"engine": "argument_map", "input_key": "argument", "output_key": "argument_structure"},
        {"engine": "replication_predict", "input_key": "finding", "output_key": "replication"},
        {"engine": "epistemic_bias_landscape", "input_key": "domain", "output_key": "biases"},
        {"engine": "insight_crystallize", "input_key": "question", "extra_input": {"intelligence": "collect_all"}, "output_key": "crystal"},
    ],
    "literature_scan": [
        {"engine": "temporal_momentum", "input_key": "topic", "output_key": "momentum"},
        {"engine": "consensus_map", "input_key": "question", "output_key": "consensus"},
        {"engine": "lineage_trace", "input_key": "concept", "output_key": "lineage"},
        {"engine": "graph_analyze_structure", "input_key": "query", "output_key": "structure"},
    ],
    "epistemic_audit": [
        {"engine": "epistemic_status_map", "input_key": "topic", "output_key": "status"},
        {"engine": "assumption_excavate", "input_key": "argument", "output_key": "assumptions"},
        {"engine": "evidence_chain_trace", "input_key": "claim", "output_key": "chain"},
        {"engine": "falsification_design", "input_key": "claim", "output_key": "falsification"},
        {"engine": "confidence_calibrate", "input_key": "claims", "output_key": "calibration"},
        {"engine": "steelman_build", "input_key": "position", "output_key": "steelman"},
    ],
    "structured_investigation": [
        {"engine": "question_decompose", "input_key": "question", "output_key": "decomposition"},
        {"engine": "gap_find", "input_key": "topic", "output_key": "gaps"},
        {"engine": "precedent_find", "input_key": "situation", "output_key": "precedents"},
        {"engine": "hypothesis_generate", "input_key": "question", "output_key": "hypotheses"},
        {"engine": "methodology_recommend", "input_key": "question", "output_key": "methodology"},
        {"engine": "implication_map", "input_key": "finding", "source": "hypotheses.0.hypothesis", "output_key": "implications"},
        {"engine": "insight_crystallize", "input_key": "question", "extra_input": {"intelligence": "collect_all"}, "output_key": "crystal"},
    ],
    "critical_evaluation": [
        {"engine": "bias_detect", "input_key": "argument", "output_key": "biases"},
        {"engine": "counterexample_generate", "input_key": "claim", "output_key": "counterexamples"},
        {"engine": "uncertainty_quantify", "input_key": "claim", "output_key": "uncertainty"},
        {"engine": "sensitivity_analyze", "input_key": "conclusion", "output_key": "sensitivity"},
        {"engine": "red_team", "input_key": "proposal", "output_key": "red_team"},
        {"engine": "mechanism_explain", "input_key": "phenomenon", "output_key": "mechanism"},
    ],
}


class ResearchWorkflowService:
    """Executes automated multi-engine research pipelines."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_workflow(
        self,
        workflow: str,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Execute a predefined workflow template."""
        from app.services.agent.tool_dispatcher import ToolDispatcher

        if workflow not in WORKFLOW_TEMPLATES:
            return {
                "error": f"Unknown workflow: {workflow}",
                "available": list(WORKFLOW_TEMPLATES.keys()),
            }

        template = WORKFLOW_TEMPLATES[workflow]
        dispatcher = ToolDispatcher(self.db)
        results = []
        context = {"question": question, "domain": domain, "dossier_id": dossier_id}

        for step in template:
            engine = step["engine"]
            args = self._build_args(step, question, domain, context, results)

            try:
                result = await dispatcher.call_tool(engine, args)
                results.append({"engine": engine, "result": result})
                self._update_context(context, step.get("output_key", ""), result)
            except Exception as e:
                results.append({"engine": engine, "error": str(e)})

        executive = await self._synthesize_results(question, results)

        return {
            "workflow": workflow,
            "question": question,
            "steps_completed": len([r for r in results if "error" not in r]),
            "steps_total": len(template),
            "step_results": [
                {"engine": r["engine"], "success": "error" not in r}
                for r in results
            ],
            "executive_summary": executive,
        }

    async def list_workflows(self) -> dict:
        """List available workflow templates."""
        return {
            "workflows": {
                name: {
                    "steps": len(template),
                    "engines": [s["engine"] for s in template],
                }
                for name, template in WORKFLOW_TEMPLATES.items()
            }
        }

    def _build_args(self, step: dict, question: str, domain: str, context: dict, results: list) -> dict:
        args = {"domain": domain}
        input_key = step["input_key"]

        source = step.get("source")
        if source and results:
            val = self._resolve_source(source, results, context)
            if val:
                args[input_key] = val
            else:
                args[input_key] = question
        else:
            args[input_key] = question

        if step.get("extra_input", {}).get("intelligence") == "collect_all":
            summaries = []
            for r in results:
                if "error" not in r:
                    res = r["result"]
                    if isinstance(res, dict):
                        for k, v in res.items():
                            if isinstance(v, str) and len(v) > 20:
                                summaries.append(f"[{r['engine']}] {v[:150]}")
                                break
            args["intelligence"] = summaries or [question]

        if "dossier_id" in context and context["dossier_id"]:
            args["dossier_id"] = context["dossier_id"]

        return args

    def _resolve_source(self, source: str, results: list, context: dict) -> str | None:
        parts = source.split(".")
        if not parts:
            return None
        key = parts[0]
        for r in results:
            if r.get("engine", "").endswith(key) or key in str(r.get("result", {}).keys()):
                val = r.get("result", {})
                for p in parts[1:]:
                    if isinstance(val, dict):
                        val = val.get(p, val)
                    elif isinstance(val, list) and p.isdigit():
                        idx = int(p)
                        val = val[idx] if idx < len(val) else val
                    else:
                        break
                if isinstance(val, str):
                    return val
                elif isinstance(val, dict):
                    return str(val.get("hypothesis", val.get("text", str(val)[:200])))
                elif isinstance(val, list):
                    return [str(v)[:100] if not isinstance(v, str) else v for v in val[:10]]
        return None

    def _update_context(self, context: dict, key: str, result) -> None:
        if key and isinstance(result, dict):
            context[key] = result

    async def _synthesize_results(self, question: str, results: list) -> str:
        summaries = []
        key_priority = [
            "core_insight", "bottom_line", "overall_score", "verdict",
            "replication_probability", "overall_impact", "current_phase",
            "overall_validity", "reasoning_quality", "consistency_score",
            "freshness_score", "field_position", "grade",
        ]
        for r in results:
            if "error" not in r:
                res = r["result"]
                if isinstance(res, dict):
                    for k in key_priority:
                        if k in res:
                            summaries.append(f"{r['engine']}: {k}={res[k]}")
                            break
                    else:
                        for k, v in res.items():
                            if isinstance(v, (int, float, str)) and v and k not in ("question", "topic", "domain", "finding"):
                                summaries.append(f"{r['engine']}: {k}={str(v)[:60]}")
                                break
        return " | ".join(summaries) or "Workflow completed"
