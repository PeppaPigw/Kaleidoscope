"""Workflow-level contracts for autonomous research agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.services.agent_endpoint_profiles import (
    DEFAULT_PAPER_ID,
    DEFAULT_TOPIC,
)

WorkflowStatus = Literal["production", "beta", "planned"]


@dataclass(frozen=True)
class AgentWorkflowStep:
    """One executable step in a research-agent workflow."""

    id: str
    name: str
    method: str
    path: str
    required: bool = True
    why: str = ""
    input_from: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    failure_recovery: str = ""

    @property
    def endpoint(self) -> str:
        return f"{self.method.upper()} {self.path}"

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": self.endpoint,
            "method": self.method.upper(),
            "path": self.path,
            "required": self.required,
            "why": self.why,
            "input_from": list(self.input_from),
            "produces": list(self.produces),
            "success_criteria": list(self.success_criteria),
            "failure_recovery": self.failure_recovery,
        }


@dataclass(frozen=True)
class AgentWorkflowProfile:
    """Task-level contract that chains endpoint contracts into useful work."""

    id: str
    title: str
    status: WorkflowStatus
    goal: str
    entry_inputs: tuple[str, ...]
    steps: tuple[AgentWorkflowStep, ...]
    final_deliverable: str
    failure_modes: tuple[dict[str, Any], ...] = ()
    example_entry: dict[str, Any] = field(default_factory=dict)

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "goal": self.goal,
            "entry_inputs": list(self.entry_inputs),
            "steps": [step.manifest_entry() for step in self.steps],
            "final_deliverable": self.final_deliverable,
            "failure_modes": list(self.failure_modes),
            "example_entry": self.example_entry,
        }


DEFAULT_WORKFLOW_FAILURE_MODES = (
    {
        "code": "INSUFFICIENT_LOCAL_CORPUS",
        "meaning": "The workflow cannot find enough local evidence to finish reliably.",
        "agent_action": "Import or process more papers, or broaden topic scope.",
    },
    {
        "code": "STEP_CONTRACT_FAILED",
        "meaning": "A required workflow step did not produce its declared output contract.",
        "agent_action": "Stop the workflow, inspect the failing step report, then use the declared fallback.",
    },
)


def _entry(*, task: str | None = None, claim: str | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "topic": DEFAULT_TOPIC,
        "paper_ids": [DEFAULT_PAPER_ID],
    }
    if task:
        entry["task"] = task
    if claim:
        entry["claim"] = claim
        entry["claims"] = [claim]
    return entry


WORKFLOWS: tuple[AgentWorkflowProfile, ...] = (
    AgentWorkflowProfile(
        id="grounded_literature_review",
        title="Build a Grounded Literature Review",
        status="production",
        goal="Create a cited literature-review plan from a topic or seed papers.",
        entry_inputs=("topic", "paper_ids", "collection_id"),
        example_entry=_entry(task="write a grounded literature review"),
        final_deliverable="Evidence-backed outline, grounded claims, and bibliography entries.",
        failure_modes=DEFAULT_WORKFLOW_FAILURE_MODES,
        steps=(
            AgentWorkflowStep(
                id="discover_capabilities",
                name="Discover agent capabilities",
                method="GET",
                path="/api/v1/agent/capabilities",
                why="Confirm which production endpoints can be used in this deployment.",
                produces=("data.capabilities", "data.recommended_workflows"),
                success_criteria=("data.capabilities is non-empty",),
            ),
            AgentWorkflowStep(
                id="collect_evidence",
                name="Collect evidence",
                method="POST",
                path="/api/v1/agent/evidence/search",
                why="Fetch grounded snippets before synthesis or writing.",
                input_from=("entry.topic", "entry.paper_ids"),
                produces=("evidence",),
                success_criteria=("evidence is non-empty",),
                failure_recovery="Broaden topic scope or ingest additional papers.",
            ),
            AgentWorkflowStep(
                id="build_context",
                name="Build task context",
                method="POST",
                path="/api/v1/agent/context/task-pack",
                why="Package bounded context blocks and next tool suggestions for a writing task.",
                input_from=("collect_evidence.evidence[].paper_id", "entry.task"),
                produces=("data.context_blocks", "data.tool_suggestions"),
                success_criteria=("data.context_blocks is non-empty",),
                failure_recovery="Use evidence/search directly or reduce token budget pressure.",
            ),
            AgentWorkflowStep(
                id="build_matrix",
                name="Build evidence matrix",
                method="POST",
                path="/api/v1/agent/synthesis/evidence-matrix",
                why="Convert evidence into a claim-by-paper support table.",
                input_from=("build_context.data.context_blocks",),
                produces=("data.matrix", "data.claims"),
                success_criteria=("data.matrix is present",),
            ),
            AgentWorkflowStep(
                id="ground_claims",
                name="Ground writing claims",
                method="POST",
                path="/api/v1/agent/writing/claim-grounding",
                why="Separate grounded claims from unsupported claims before drafting.",
                input_from=("build_context.data.context_blocks",),
                produces=("data.grounded_claims", "data.unsupported_claims"),
                success_criteria=("data.grounded_claims or data.unsupported_claims is present",),
            ),
            AgentWorkflowStep(
                id="export_bibliography",
                name="Export bibliography",
                method="POST",
                path="/api/v1/agent/writing/bibliography/export",
                why="Produce citation entries for grounded outputs.",
                input_from=("entry.paper_ids",),
                produces=("data.entries",),
                success_criteria=("data.entries is non-empty",),
            ),
        ),
    ),
    AgentWorkflowProfile(
        id="read_one_paper",
        title="Read and Understand One Paper",
        status="production",
        goal="Turn one paper into exact structure, evidence, and reusable scientific cards.",
        entry_inputs=("paper_id",),
        example_entry=_entry(),
        final_deliverable="Section map, paragraph evidence, method card, experiment card, result card, and limitations.",
        failure_modes=DEFAULT_WORKFLOW_FAILURE_MODES,
        steps=(
            AgentWorkflowStep(
                id="map_sections",
                name="Map sections",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/section-map",
                why="Select exact paper regions before reading details.",
                input_from=("entry.paper_id",),
                produces=("data.sections",),
                success_criteria=("data.sections is non-empty",),
            ),
            AgentWorkflowStep(
                id="read_introduction",
                name="Read introduction",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/sections/{section_type}",
                input_from=("map_sections.data.sections[].normalized_type",),
                produces=("data.markdown", "data.paragraphs"),
                success_criteria=("data.paragraphs is non-empty",),
            ),
            AgentWorkflowStep(
                id="read_paragraphs",
                name="Read paragraph anchors",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/paragraphs",
                produces=("data.paragraphs",),
                success_criteria=("data.paragraphs is non-empty",),
            ),
            AgentWorkflowStep(
                id="method_card",
                name="Extract method card",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/method-card",
                produces=("data.method_name", "data.inputs", "data.outputs"),
                success_criteria=("data.method_name is present",),
            ),
            AgentWorkflowStep(
                id="experiment_card",
                name="Extract experiment card",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/experiment-card",
                produces=("data.datasets", "data.metrics"),
                success_criteria=("data.metrics is present",),
            ),
            AgentWorkflowStep(
                id="results_card",
                name="Extract results card",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/results-card",
                produces=("data.results",),
                success_criteria=("data.results is present",),
            ),
        ),
    ),
    AgentWorkflowProfile(
        id="verify_scientific_claim",
        title="Verify a Scientific Claim",
        status="production",
        goal="Decide whether a claim is supported, refuted, or insufficiently evidenced.",
        entry_inputs=("claim", "paper_ids", "topic"),
        example_entry=_entry(claim=DEFAULT_TOPIC),
        final_deliverable="Claim label, confidence, evidence pack, and missing-evidence diagnostics.",
        failure_modes=DEFAULT_WORKFLOW_FAILURE_MODES,
        steps=(
            AgentWorkflowStep(
                id="search_claim_evidence",
                name="Search claim evidence",
                method="POST",
                path="/api/v1/agent/evidence/search",
                input_from=("entry.claim", "entry.paper_ids"),
                produces=("evidence",),
                success_criteria=("evidence is non-empty",),
            ),
            AgentWorkflowStep(
                id="pack_claim_evidence",
                name="Pack claim evidence",
                method="POST",
                path="/api/v1/agent/evidence/packs",
                input_from=("search_claim_evidence.evidence",),
                produces=("evidence", "citations"),
                success_criteria=("evidence is non-empty",),
            ),
            AgentWorkflowStep(
                id="verify_claim",
                name="Verify claim",
                method="POST",
                path="/api/v1/agent/claims/verify",
                input_from=("entry.claim", "pack_claim_evidence.evidence"),
                produces=("label", "confidence", "evidence_pack"),
                success_criteria=("label is present", "evidence_pack.evidence is non-empty"),
            ),
            AgentWorkflowStep(
                id="map_claim_to_paper_evidence",
                name="Map claim to paper evidence",
                method="POST",
                path="/api/v1/agent/papers/{paper_id}/claim-to-evidence-map",
                input_from=("entry.claims", "entry.paper_id"),
                produces=("data.claim_evidence",),
                success_criteria=("data.claim_evidence is present",),
            ),
        ),
    ),
    AgentWorkflowProfile(
        id="compare_methods",
        title="Compare Methods Across Papers",
        status="production",
        goal="Compare methods and identify tradeoffs, gaps, and a reading plan.",
        entry_inputs=("topic", "paper_ids", "collection_id"),
        example_entry=_entry(task="compare methods across papers"),
        final_deliverable="Method comparison, evidence matrix, gap analysis, and reading plan.",
        failure_modes=DEFAULT_WORKFLOW_FAILURE_MODES,
        steps=(
            AgentWorkflowStep(
                id="build_evidence_matrix",
                name="Build evidence matrix",
                method="POST",
                path="/api/v1/agent/synthesis/evidence-matrix",
                produces=("data.matrix",),
                success_criteria=("data.matrix is present",),
            ),
            AgentWorkflowStep(
                id="compare_methods",
                name="Compare methods",
                method="POST",
                path="/api/v1/agent/synthesis/method-comparison",
                produces=("data.methods", "data.tradeoffs"),
                success_criteria=("data.methods is present",),
            ),
            AgentWorkflowStep(
                id="find_gaps",
                name="Find research gaps",
                method="POST",
                path="/api/v1/agent/synthesis/gap-analysis",
                produces=("data.gaps", "data.suggested_work"),
                success_criteria=("data.gaps is present",),
            ),
            AgentWorkflowStep(
                id="make_reading_plan",
                name="Make reading plan",
                method="POST",
                path="/api/v1/agent/synthesis/reading-plan",
                produces=("data.steps", "data.paper_ids"),
                success_criteria=("data.steps is present",),
            ),
        ),
    ),
    AgentWorkflowProfile(
        id="plan_reproduction",
        title="Plan Reproduction",
        status="production",
        goal="Inspect artifacts and create a concrete reproduction plan for one paper.",
        entry_inputs=("paper_id",),
        example_entry=_entry(task="replicate the paper results"),
        final_deliverable="Artifact inventory, environment spec, reproduction checklist, and replication plan.",
        failure_modes=DEFAULT_WORKFLOW_FAILURE_MODES,
        steps=(
            AgentWorkflowStep(
                id="source_provenance",
                name="Inspect source provenance",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/source-provenance",
                produces=("data.source_urls", "data.external_ids"),
                success_criteria=("data.external_ids is present",),
            ),
            AgentWorkflowStep(
                id="artifact_links",
                name="List artifacts",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/artifact-links",
                produces=("data.artifacts",),
                success_criteria=("data.artifacts is present",),
            ),
            AgentWorkflowStep(
                id="repo_summary",
                name="Summarize repository",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/repo/summary",
                produces=("data.repo_url", "data.entrypoints"),
                success_criteria=("data.entrypoints is present",),
            ),
            AgentWorkflowStep(
                id="environment_spec",
                name="Extract environment spec",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/environment-spec",
                produces=("data.python", "data.packages", "data.hardware"),
                success_criteria=("data.packages is present",),
            ),
            AgentWorkflowStep(
                id="repro_checklist",
                name="Build reproducibility checklist",
                method="GET",
                path="/api/v1/agent/papers/{paper_id}/reproducibility-checklist",
                produces=("data.checklist", "data.missing_artifacts"),
                success_criteria=("data.checklist is present",),
            ),
            AgentWorkflowStep(
                id="replication_plan",
                name="Generate replication plan",
                method="POST",
                path="/api/v1/agent/papers/{paper_id}/replication-plan",
                produces=("data.steps", "data.environment", "data.validation_metrics"),
                success_criteria=("data.steps is present",),
            ),
        ),
    ),
)


def iter_agent_workflow_profiles() -> tuple[AgentWorkflowProfile, ...]:
    """Return all workflow-level contracts."""
    return WORKFLOWS


def workflow_by_id(workflow_id: str) -> AgentWorkflowProfile | None:
    """Return one workflow contract by id."""
    return next((workflow for workflow in WORKFLOWS if workflow.id == workflow_id), None)


def workflow_refs_for_endpoint(endpoint: str) -> tuple[str, ...]:
    """Return workflow ids that include an endpoint key."""
    return tuple(
        workflow.id
        for workflow in WORKFLOWS
        if any(step.endpoint == endpoint for step in workflow.steps)
    )
