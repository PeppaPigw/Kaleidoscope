"""Paper Links Service — AI-powered supplementary link discovery.

Calls the Grok API with a paper title to discover:
  - venue (journal / conference)
  - code_url
  - dataset_urls
  - model_weights_url
  - project_page_url
  - related_links (blog_url, discussion_url, social_url)

Credentials come from settings (links_api_url, links_api_key, links_model).
"""

from __future__ import annotations

import json
import re

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_PROMPT_TEMPLATE = (
    "You are a research assistant. Given a paper title and identifiers, return ONLY a valid JSON object "
    "(no explanations, no markdown fences, no extra text). "
    "The JSON must include exactly these fields: "
    "venue (the journal or conference where the paper is published or submitted), "
    "code_url (the official code repository URL, e.g. GitHub), "
    "dataset_urls (array of dataset URLs used or released by this paper, e.g. HuggingFace/Zenodo), "
    "model_weights_url (URL to model weights or checkpoints, e.g. HuggingFace), "
    "project_page_url (the paper's primary public URL — if no dedicated project page exists, "
    "use the arXiv abstract page or DOI resolver URL from the identifiers provided below), "
    "related_links (object with blog_url, discussion_url, social_url). "
    "Return null for any field you cannot find. "
    "Ensure the output is strictly valid JSON.\n\n"
    'Paper title: "{title}"\n'
    "{identifiers}"
)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> dict:
    """Extract JSON from response text, stripping markdown fences if present."""
    # Try stripping code fences first
    m = _JSON_FENCE_RE.search(text)
    raw = m.group(1).strip() if m else text.strip()
    return json.loads(raw)


def _extract_content(response_json: dict) -> str:
    """Extract text content from OpenAI or Anthropic response format."""
    # OpenAI: choices[0].message.content
    choices = response_json.get("choices")
    if choices and isinstance(choices, list):
        msg = choices[0].get("message", {})
        return msg.get("content", "")
    # Anthropic: content[0].text
    content = response_json.get("content")
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return ""


class LinksService:
    """Fetch AI-powered paper links for a given paper title."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> LinksService:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def fetch_links(
        self,
        title: str,
        arxiv_id: str | None = None,
        doi: str | None = None,
    ) -> dict:
        """
        Call Grok API with the paper title.

        Returns a dict with: venue, code_url, dataset_urls, model_weights_url,
        project_page_url, related_links.  All fields may be None.

        Raises on HTTP / parse errors — callers should catch.
        """
        if not settings.links_api_key:
            raise RuntimeError("links_api_key not configured")

        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
        doi_url = f"https://doi.org/{doi}" if doi else None

        id_lines: list[str] = []
        if arxiv_id:
            id_lines.append(f"arXiv ID: {arxiv_id} (URL: {arxiv_url})")
        if doi:
            id_lines.append(f"DOI: {doi} (URL: {doi_url})")

        prompt = _PROMPT_TEMPLATE.format(
            title=title.replace('"', "'"),
            identifiers=(
                "\n".join(id_lines) if id_lines else "(no identifiers available)"
            ),
        )
        payload = {
            "model": settings.links_model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Authorization": f"Bearer {settings.links_api_key}",
            "Content-Type": "application/json",
        }

        client = await self._get_client()
        resp = await client.post(settings.links_api_url, json=payload, headers=headers)
        resp.raise_for_status()

        raw_text = _extract_content(resp.json())
        if not raw_text:
            raise ValueError("Empty response content from links API")

        data = _extract_json(raw_text)

        # Normalise — ensure all expected top-level keys are present
        related = data.get("related_links") or {}
        project_page = data.get("project_page_url") or None
        # Hard fallback: arXiv URL → DOI URL when the model returns nothing
        if not project_page and arxiv_url:
            project_page = arxiv_url
        elif not project_page and doi_url:
            project_page = doi_url
        return {
            "venue": data.get("venue") or None,
            "code_url": data.get("code_url") or None,
            "dataset_urls": data.get("dataset_urls") or None,
            "model_weights_url": data.get("model_weights_url") or None,
            "project_page_url": project_page,
            "related_links": {
                "blog_url": related.get("blog_url") or None,
                "discussion_url": related.get("discussion_url") or None,
                "social_url": related.get("social_url") or None,
            },
        }
