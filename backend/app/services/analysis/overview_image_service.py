"""OverviewImageService — 一图速览 poster generation for a paper.

Workflow:
1. Use paper.deep_analysis["analysis"] as content input.
2. Call the LLM (via LLMClient) to produce a structured visual-summary brief (JSON).
3. Call the image generation API via curl subprocess to produce a poster image.
4. Upload the image bytes to Aliyun OSS.
5. Return the public URL.

The caller stores the result in Paper.overview_image (JSONB).
"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from functools import partial
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# ── Reuse prompts from the standalone script ──────────────────────────────────
from app.services.analysis.generate_overall_image import (
    DEFAULT_IMAGE_GENERATION_PROMPT,
    DEFAULT_IMAGE_SUMMARY_PROMPT,
    DEFAULT_ASPECT_RATIO,
    DEFAULT_TEXT_DENSITY_MODE,
    DEFAULT_MAX_CONTEXT_CHARS,
    ImageGenerationResult,
    PipelineError,
    decode_base64_bytes,
    extract_text_from_chat_content,
    iter_all_strings,
    try_extract_image_result_from_text,
    normalize_endpoint,
    parse_image_response,
    suffix_for_mime,
)


def _truncate(text: str, max_len: int = DEFAULT_MAX_CONTEXT_CHARS) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for ch in ("。", ".", "！", "!", "？", "?"):
        idx = cut.rfind(ch)
        if idx > max_len * 0.8:
            return cut[: idx + 1]
    return cut


def _build_visual_summary_prompt(title: str, content: str) -> str:
    return DEFAULT_IMAGE_SUMMARY_PROMPT.format(
        title=title,
        context=_truncate(content),
    )


def _build_image_prompt(title: str, visual_summary: str) -> str:
    return DEFAULT_IMAGE_GENERATION_PROMPT.format(
        title=title,
        summary_for_image=visual_summary.strip(),
        aspect_ratio=DEFAULT_ASPECT_RATIO,
        text_density_mode=DEFAULT_TEXT_DENSITY_MODE,
    )


def _call_image_api_sync(
    endpoint: str, api_key: str, model: str, prompt: str
) -> ImageGenerationResult:
    """Synchronous image API call via curl (run in thread pool by the async wrapper)."""
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "tools": [{"type": "image_generation"}],
    }

    cmd = [
        "curl",
        "-sS",
        "--max-time",
        "300",
        "-X",
        "POST",
        endpoint,
        "-H",
        "Content-Type: application/json",
    ]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-d", json.dumps(payload, ensure_ascii=False)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PipelineError(f"curl failed ({result.returncode}): {result.stderr[:500]}")
    raw = result.stdout.strip()
    if not raw:
        raise PipelineError("curl returned empty response")
    try:
        response = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Invalid JSON from image API: {raw[:500]}") from exc
    return parse_image_response(response)


class OverviewImageService:
    """Generate a 一图速览 poster and upload it to OSS."""

    def __init__(self) -> None:
        self._llm: Any = None

    async def _get_llm(self):
        if self._llm is None:
            from app.clients.llm_client import LLMClient

            self._llm = LLMClient()
        return self._llm

    async def generate(self, paper_title: str, analysis_text: str) -> str:
        """
        Run the full pipeline and return the public OSS URL of the poster.

        Raises PipelineError on failure.
        """
        log = logger.bind(title=paper_title[:60])

        # 1. LLM → visual summary brief
        log.info("overview_image_llm_start")
        summary_prompt = _build_visual_summary_prompt(paper_title, analysis_text)
        llm = await self._get_llm()
        visual_summary = await llm.complete(
            prompt=summary_prompt,
            system="You are a precise research summarization assistant.",
            temperature=0.2,
            max_tokens=4096,
            enable_thinking=True,
        )
        if not visual_summary.strip():
            raise PipelineError("LLM returned empty visual summary")
        log.info("overview_image_llm_done", chars=len(visual_summary))

        # 2. Build image prompt
        image_prompt = _build_image_prompt(paper_title, visual_summary)

        # 3. Image API (curl in thread pool to avoid blocking event loop)
        log.info("overview_image_api_start")
        endpoint = normalize_endpoint(settings.image_api_url, "/v1/responses")
        loop = asyncio.get_running_loop()
        image_result: ImageGenerationResult = await loop.run_in_executor(
            None,
            partial(
                _call_image_api_sync,
                endpoint,
                settings.image_api_key,
                settings.image_model,
                image_prompt,
            ),
        )
        log.info(
            "overview_image_api_done",
            bytes=len(image_result.image_bytes),
            mime=image_result.mime_type,
        )

        # 4. Upload to OSS
        from app.clients.oss_client import OssClient

        ext = suffix_for_mime(image_result.mime_type)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        object_key = f"Kaleidoscope/overview-images/{ts}{ext}"

        async with OssClient() as oss:
            url = await oss.upload_bytes(image_result.image_bytes, object_key)

        log.info("overview_image_uploaded", url=url)
        return url

    async def close(self) -> None:
        if self._llm:
            try:
                await self._llm.close()
            except Exception:
                pass
