"""Paper labeling service — assign structured taxonomy tags via LLM.

This is a standalone LLM call intentionally separate from other analysis
tasks (deep analysis, summarization) to avoid overloading a single request.

Input:  paper full text (via TextChunker.prepare_paper_text)
Output: structured labels across 5 user-facing dimensions + 3 meta dimensions,
        stored in paper.paper_labels (JSONB).

Schema:
{
  "domain": [],
  "task": [],
  "method": [],
  "data_object": [],
  "application": [],
  "meta": {
    "paper_type": [],
    "evaluation_quality": [],
    "resource_constraint": []
  }
}
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.llm_client import LLMClient
from app.models.paper import Paper
from app.services.extraction.chunker import TextChunker

logger = structlog.get_logger(__name__)

# Taxonomy file lives at <repo_root>/frontend/public/labels.json
_TAXONOMY_PATH = Path(__file__).parents[4] / "frontend" / "public" / "labels.json"

# Full-text truncation limit (words) — enough for labeling without burning tokens
_MAX_TEXT_WORDS = 8000


def labels_have_any_values(labels: dict | None) -> bool:
    """Return True when at least one taxonomy bucket contains a label."""
    if not isinstance(labels, dict):
        return False

    meta = labels.get("meta") or {}
    groups = (
        labels.get("domain"),
        labels.get("task"),
        labels.get("method"),
        labels.get("data_object"),
        labels.get("application"),
        meta.get("paper_type"),
        meta.get("evaluation_quality"),
        meta.get("resource_constraint"),
    )
    return any(bool(group) for group in groups)


def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _flatten(node: dict | list) -> list[str]:
    """Recursively collect all leaf strings from a nested dict/list."""
    out: list[str] = []
    if isinstance(node, list):
        for v in node:
            if isinstance(v, str):
                out.append(v)
            else:
                out.extend(_flatten(v))
    elif isinstance(node, dict):
        for v in node.values():
            out.extend(_flatten(v))
    return out


def _build_prompt(paper: Paper, fulltext: str, taxonomy: dict) -> str:
    tag_system = taxonomy["TagSystem"]
    user_tags = tag_system["UserTag"]
    meta_tags = tag_system["MetaTag"]

    domain_vals = _flatten(user_tags.get("Domain", {}))
    task_vals = _flatten(user_tags.get("Task", {}))
    method_vals = _flatten(user_tags.get("Method", {}))
    data_vals = _flatten(user_tags.get("Data_Object", {}))
    app_vals = _flatten(user_tags.get("Application", {}))

    paper_type_vals = meta_tags.get("Paper Type", [])
    eval_vals = meta_tags.get("Evaluation / Quality", [])
    resource_vals = meta_tags.get("Resource / Constraint", [])

    title = paper.title or "(no title)"
    abstract_block = f"Abstract:\n{paper.abstract}\n\n" if paper.abstract else ""

    words = fulltext.split()
    if len(words) > _MAX_TEXT_WORDS:
        fulltext = " ".join(words[:_MAX_TEXT_WORDS]) + "\n[... truncated]"

    text_block = (
        fulltext
        if fulltext
        else "(full text unavailable — use title and abstract only)"
    )

    return f"""You are a scientific paper classifier. Read the paper below and assign taxonomy labels.

PAPER:
Title: {title}
{abstract_block}Content:
{text_block}

---
TAXONOMY — select ONLY values from these lists (pick all that apply per dimension):

domain: {json.dumps(domain_vals)}

task: {json.dumps(task_vals)}

method: {json.dumps(method_vals)}

data_object: {json.dumps(data_vals)}

application: {json.dumps(app_vals)}

meta.paper_type: {json.dumps(paper_type_vals)}
meta.evaluation_quality: {json.dumps(eval_vals)}
meta.resource_constraint: {json.dumps(resource_vals)}

---
Return ONLY a valid JSON object, no markdown fences, no explanation:
{{
  "domain": [],
  "task": [],
  "method": [],
  "data_object": [],
  "application": [],
  "meta": {{
    "paper_type": [],
    "evaluation_quality": [],
    "resource_constraint": []
  }}
}}

Rules:
- Use EXACT strings from the lists above.
- Each dimension may have zero or more values.
- Do NOT invent tags outside the taxonomy.
"""


def _parse_response(raw: str) -> dict:
    """Extract JSON dict from LLM response, stripping any markdown fences."""
    # Strip ```json ... ``` fences
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Find the outermost {...}
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in LLM response: {raw[:200]}")
    return json.loads(raw[start:end])


def _validate_labels(labels: dict, taxonomy: dict) -> dict:
    """
    Validate and filter labels — remove any values not in the taxonomy.
    Returns a clean labels dict.
    """
    tag_system = taxonomy["TagSystem"]
    user_tags = tag_system["UserTag"]
    meta_tags = tag_system["MetaTag"]

    valid_domain = set(_flatten(user_tags.get("Domain", {})))
    valid_task = set(_flatten(user_tags.get("Task", {})))
    valid_method = set(_flatten(user_tags.get("Method", {})))
    valid_data = set(_flatten(user_tags.get("Data_Object", {})))
    valid_app = set(_flatten(user_tags.get("Application", {})))
    valid_paper_type = set(meta_tags.get("Paper Type", []))
    valid_eval = set(meta_tags.get("Evaluation / Quality", []))
    valid_resource = set(meta_tags.get("Resource / Constraint", []))

    def keep(raw: list, valid: set) -> list[str]:
        return [v for v in (raw or []) if v in valid]

    meta = labels.get("meta", {})
    return {
        "domain": keep(labels.get("domain", []), valid_domain),
        "task": keep(labels.get("task", []), valid_task),
        "method": keep(labels.get("method", []), valid_method),
        "data_object": keep(labels.get("data_object", []), valid_data),
        "application": keep(labels.get("application", []), valid_app),
        "meta": {
            "paper_type": keep(meta.get("paper_type", []), valid_paper_type),
            "evaluation_quality": keep(meta.get("evaluation_quality", []), valid_eval),
            "resource_constraint": keep(
                meta.get("resource_constraint", []), valid_resource
            ),
        },
    }


def _make_default_llm() -> tuple[LLMClient, str]:
    """
    Return a (LLMClient, model_name) pair using the best available credentials.

    Priority:
      1. BLSC/primary LLM (settings.llm_api_key + settings.llm_base_url)
      2. Translate API (settings.translate_api_key + settings.translate_base_url)
         — known-working NVIDIA endpoint used for translations
    """
    from app.config import settings

    if settings.llm_api_key:
        return LLMClient(), settings.llm_model

    if getattr(settings, "translate_api_key", None):
        base = settings.translate_base_url.rstrip("/") + "/v1"
        return (
            LLMClient(api_key=settings.translate_api_key, base_url=base),
            settings.translate_model,
        )

    raise RuntimeError(
        "No LLM API credentials configured (llm_api_key or translate_api_key required)"
    )


class LabelingService:
    """Assign structured taxonomy labels to a paper via LLM."""

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMClient | None = None,
        model: str | None = None,
    ):
        self.db = db
        if llm is not None:
            self.llm = llm
            self._model = model
        else:
            self.llm, default_model = _make_default_llm()
            self._model = model or default_model
        self._taxonomy: dict | None = None

    def _get_taxonomy(self) -> dict:
        if self._taxonomy is None:
            self._taxonomy = _load_taxonomy()
        return self._taxonomy

    async def label_paper(self, paper: Paper, force: bool = False) -> dict:
        """
        Generate and persist labels for a paper.

        Args:
            paper:  ORM Paper instance (must be attached to a session).
            force:  Re-label even if paper_labels is already populated.

        Returns:
            The labels dict that was persisted.
        """
        log = logger.bind(paper_id=str(paper.id))

        if paper.paper_labels and not force:
            if labels_have_any_values(paper.paper_labels):
                log.info("labeling_skipped", reason="already_labeled")
                return paper.paper_labels
            log.info("labeling_retrying", reason="stale_empty_labels")

        taxonomy = self._get_taxonomy()
        fulltext = TextChunker.prepare_paper_text(paper)
        title = (paper.title or "").strip()
        source_text = fulltext.strip() or (paper.abstract or "").strip()

        if not title:
            raise ValueError("Paper title unavailable for labeling")
        if len(source_text) < 120:
            raise ValueError("Paper text unavailable for labeling")

        prompt = _build_prompt(paper, fulltext, taxonomy)

        log.info("labeling_start", fulltext_words=len(fulltext.split()))

        kwargs: dict = dict(
            prompt=prompt,
            system=(
                "You are a precise scientific classification assistant. "
                "Output only valid JSON matching the requested schema."
            ),
            max_tokens=2048,
            temperature=0.05,
        )
        if self._model:
            kwargs["model"] = self._model

        raw = await self.llm.complete(**kwargs)

        try:
            labels = _parse_response(raw)
            labels = _validate_labels(labels, taxonomy)
        except Exception as exc:
            log.error("labeling_parse_error", error=str(exc), raw=raw[:300])
            raise

        if not labels_have_any_values(labels):
            log.warning("labeling_empty_payload")
            raise ValueError("Labeling produced no taxonomy labels")

        paper.paper_labels = labels
        paper.paper_labels_at = datetime.now(timezone.utc)
        await self.db.flush()

        log.info(
            "labeling_done",
            domain_count=len(labels.get("domain", [])),
            task_count=len(labels.get("task", [])),
            method_count=len(labels.get("method", [])),
        )
        return labels

    async def close(self) -> None:
        await self.llm.close()
