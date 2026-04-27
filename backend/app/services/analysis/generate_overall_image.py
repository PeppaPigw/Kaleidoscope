#!/usr/bin/env python3
"""Generate a one-image summary poster from ``paper.md``.

This script ports the core "一图总结" workflow from the Zotero plugin into a
standalone Python entrypoint:

1. Read article content from Markdown
2. Ask an LLM for a visual-summary brief
3. Ask an image model for a poster image
4. Decode the returned base64/data URL into an image file
5. Save the summary, final prompt, image, and a manifest locally
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import mimetypes
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_PAPER_PATH = "paper.md"
DEFAULT_OUTPUT_DIR = "image_output"

# Read from app settings (populated from .env) so no credentials are hardcoded.
try:
    from app.config import settings as _settings

    LLM_API_URL = _settings.llm_base_url + "/chat/completions"
    LLM_API_KEY = _settings.llm_api_key
    LLM_MODEL = _settings.llm_model
    IMAGE_API_URL = _settings.image_api_url
    IMAGE_API_KEY = _settings.image_api_key
    IMAGE_MODEL = _settings.image_model
except Exception:
    # Fallback for standalone script usage outside the app context
    LLM_API_URL = os.getenv("LLM_BASE_URL") + "/chat/completions"
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL")
    IMAGE_API_URL = os.getenv("IMAGE_API_URL")
    IMAGE_API_KEY = os.getenv("IMAGE_API_KEY")
    IMAGE_MODEL = os.getenv("IMAGE_MODEL")

LLM_ENABLE_THINKING = True

DEFAULT_LLM_BASE_URL = LLM_API_URL
DEFAULT_IMAGE_BASE_URL = IMAGE_API_URL
DEFAULT_LLM_API_KEY = LLM_API_KEY
DEFAULT_IMAGE_API_KEY = IMAGE_API_KEY
DEFAULT_LLM_MODEL = LLM_MODEL
DEFAULT_IMAGE_MODEL = IMAGE_MODEL
DEFAULT_MAX_CONTEXT_CHARS = 100_000
DEFAULT_ASPECT_RATIO = "4:3"
DEFAULT_TEXT_DENSITY_MODE = "balanced"

MARKDOWN_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<url>https?://[^)\s]+)(?:\s+\"(?P<title>[^\"]*)\")?\)"
)
HTML_IMAGE_RE = re.compile(
    r"<img[^>]+src=[\"'](?P<url>https?://[^\"']+)[\"'][^>]*?(?:alt=[\"'](?P<alt>[^\"']*)[\"'])?[^>]*>",
    re.IGNORECASE,
)
DATA_URL_RE = re.compile(
    r"data:(?P<mime>image/[a-zA-Z0-9.+-]+);base64,(?P<data>[A-Za-z0-9+/=\n\r\s]+)",
    re.IGNORECASE,
)
HTTP_URL_RE = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)


DEFAULT_IMAGE_SUMMARY_PROMPT = r"""
You are an “Academic Visualization Director + Senior Information Designer”.

Task:
Transform the input paper or technical article into a rich, execution-ready specification for a single-page academic infographic poster.

You will receive:
1. Article title
2. Article Markdown body

Goal:
Produce a structured poster brief that is both scientifically faithful and visually expressive.
The output must preserve enough information density to make the poster feel substantial, while still being clean and readable for image generation.

Core principles:
- Use only information explicitly present in the input.
- Do NOT fabricate metrics, comparisons, equations, applications, datasets, or conclusions not supported by the article.
- Preserve the paper’s scientific story, not just a minimal summary.
- Capture, when available:
  problem context, why it is hard, key idea, mechanism/pipeline, evidence/results, comparison point, limitations, significance.
- Prefer “dense but selective” over “oversimplified”.
- Translate content into visual building blocks, relationships, and poster hierarchy.
- If information is missing or weakly supported, explicitly mark it as "not explicitly provided".
- If the paper is method-focused, emphasize: motivation -> inputs -> mechanism -> outputs -> evidence -> significance.
- If the paper is theoretical or conceptual, emphasize: background -> key concept -> logical structure -> implication.
- If the paper is a survey or framework, emphasize: landscape -> taxonomy -> differences -> value.
- Reuse existing figures only at the level of composition logic or semantic structure. Never suggest copying them literally.

Strict output requirements:
- Output valid JSON only
- No markdown code block
- No commentary outside JSON
- No extra fields outside the schema

JSON schema:
{{
  "poster_goal": "One sentence describing what the viewer should understand after seeing the poster",
  "core_question": "Central research question",
  "one_sentence_takeaway": "Single strongest takeaway",
  "audience": "Primary target audience",
  "density_recommendation": "sparse / balanced / dense",
  "visual_direction": {{
    "hero_concept": "Main visual centerpiece or structural diagram concept",
    "design_mood": "e.g. editorial academic / futuristic technical / clean systems diagram",
    "palette_hint": "e.g. cool blue with one accent / neutral gray with teal accent",
    "composition_energy": "calm / balanced / dynamic"
  }},
  "scientific_story": {{
    "problem": "Problem being addressed",
    "why_it_matters": "Why the problem matters",
    "why_it_is_hard": "Main challenge or bottleneck",
    "core_idea": "Key method/viewpoint",
    "evidence": "Most important evidence or result",
    "significance": "Why the contribution matters"
  }},
  "layout_plan": {{
    "recommended_structure": "top-down / left-to-right / center-radial / comparison / timeline / hybrid",
    "reading_path": "Short description of how the eye should move across the poster",
    "hero_zone": "What should occupy the main central visual area",
    "supporting_zones": [
      "Supporting area 1",
      "Supporting area 2"
    ]
  }},
  "modules": [
    {{
      "id": "M1",
      "title": "Short section title",
      "purpose": "What this section must communicate",
      "priority": "high / medium / low",
      "size": "large / medium / small",
      "content_bullets": [
        "Short fact or phrase 1",
        "Short fact or phrase 2",
        "Short fact or phrase 3"
      ],
      "suggested_visual": "hero-diagram / flow / comparison / mechanism / chart / timeline / callout-card / icon-cluster / taxonomy",
      "must_labels": [
        "Short label 1",
        "Short label 2"
      ],
      "avoid_text": "What should not be overexplained in this module"
    }}
  ],
  "flow": [
    {{
      "from": "M1",
      "to": "M2",
      "relation": "motivates / explains / leads_to / supports / compares_with / results_in"
    }}
  ],
  "entities": [
    "Important objects, concepts, variables, components, actors, datasets, or stages"
  ],
  "must_show_relationships": [
    "Important relationship 1",
    "Important relationship 2"
  ],
  "comparison_points": [
    "Important comparison angle or contrast that should be visualized"
  ],
  "evidence_cards": [
    {{
      "claim": "Short claim",
      "evidence_type": "quantitative / qualitative / conceptual",
      "metric_or_signal": "Metric name or evidence type",
      "value": "Value or short result phrase",
      "baseline": "Baseline or comparison target, or not explicitly provided",
      "direction": "better / worse / comparable / mixed / not explicitly provided",
      "confidence": "explicit / implicit"
    }}
  ],
  "applications": [
    "Use case or impact 1",
    "Use case or impact 2"
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "reference_image_rewrite": [
    {{
      "source_hint": "Short identifier of a referenced source figure if any",
      "reuse": "Which organizational logic to absorb",
      "avoid": "What must not be copied"
    }}
  ],
  "must_include": [
    "Essential visual element 1",
    "Essential visual element 2"
  ],
  "avoid": [
    "Long paragraphs",
    "Fake metrics",
    "Decorative but irrelevant imagery",
    "Literal figure copying",
    "Visually empty sections"
  ],
  "uncertainties": [
    "Missing or weakly supported information"
  ],
  "image_text_plan": {{
    "title": "Main title text allowed in image",
    "subtitle": "Optional subtitle or none",
    "section_headers": [
      "Header 1",
      "Header 2",
      "Header 3"
    ],
    "short_labels": [
      "Short label 1",
      "Short label 2",
      "Short label 3"
    ],
    "result_badges": [
      "Very short result badge 1",
      "Very short result badge 2"
    ],
    "max_total_words": 80,
    "forbidden_long_text": true
  }}
}}

Extraction rules:
- Use 5 to 7 modules when the content supports it; never fewer than 4 unless the source is extremely short.
- Preserve both mechanism and evidence whenever available.
- Include up to 4 evidence_cards if explicitly supported.
- Keep content_bullets short and image-friendly.
- Prefer structural clarity, but do not collapse away important scientific distinctions.
- If no quantitative evidence exists, use qualitative or conceptual evidence cards instead of leaving the poster empty.
- The poster should feel informative, not skeletal.

Article title:
{title}

Markdown body:
{context}
"""


DEFAULT_IMAGE_GENERATION_PROMPT = r"""
! make sure the words in the poster are in Chinese!
Create one final single-page academic infographic poster in ultra-high resolution.

This is NOT a marketing poster.
This is a publication-quality academic visual summary with strong information hierarchy, elegant composition, and controlled information density.

Use the brief strictly.
Do not invent unsupported facts, metrics, datasets, equations, comparisons, or claims.

Article title:
{title}

Poster brief:
{summary_for_image}

Aspect ratio:
{aspect_ratio}

Text density mode:
{text_density_mode}

Primary objective:
Make the poster feel both beautiful and substantial:
- visually refined at first glance
- scientifically informative on closer inspection
- clean, not empty
- dense, not cluttered

Design intent:
- polished editorial academic poster
- strong hierarchy
- central focal figure
- clear reading path
- premium infographic feel
- restrained but memorable
- non-photorealistic
- diagram-led, vector-like, crisp
- subtle depth, layered cards, and precise technical linework
- visually sophisticated, not bland

Composition requirements:
1. Build a strong focal centerpiece in the central area:
   a hero mechanism diagram, system pipeline, conceptual map, or comparison structure.
2. Use a professional grid layout with 5 to 7 modules if the brief supports it.
3. Establish a clear reading path:
   title band -> motivation/problem -> core mechanism -> evidence/comparison -> significance/applications -> takeaway.
4. Balance whitespace with content density:
   avoid large empty zones, but preserve breathing room between sections.
5. Use visual contrast in scale:
   one dominant hero visual,
   two or three medium-support panels,
   several compact evidence or takeaway cards.
6. Convert abstract concepts into readable visual structures:
   arrows, layered boxes, pipelines, comparison cards, mini charts, timelines, icon clusters, annotated callouts.
7. If the paper contains a method:
   emphasize input -> transformation/mechanism -> output -> advantage.
8. If the paper contains comparisons or baselines:
   show them as compact comparison cards or mini bar/line/rank visuals.
9. If there are explicit results:
   show the most important 2 to 4 results as premium result badges or compact evidence cards.
10. If no strong quantitative results exist:
   emphasize conceptual structure, mechanism, qualitative findings, and practical significance instead of leaving the page visually weak.
11. Bottom area should contain a concise takeaway strip or significance band.
12. Reinterpret referenced source figures abstractly; never copy them literally.

Visual style requirements:
- elegant academic editorial aesthetic
- clean geometry
- crisp alignment
- layered information cards
- balanced asymmetry allowed
- sharp typography hierarchy
- subtle technical gradients only if they improve depth
- high contrast text on simple background
- one restrained accent color plus neutrals
- no childish icons
- no noisy textures
- no glossy ad look

Text rules:
- all text must be correctly rendered, readable, and professional
- use short labels, short section headers, and compact callouts
- avoid paragraphs
- avoid tiny illegible text
- avoid gibberish
- avoid fake citations
- avoid fake formulas
- avoid institution logos unless explicitly requested
- prefer fewer words with stronger structure

Density policy:
- sparse: fewer labels, stronger visual storytelling, only essential result cards
- balanced: strong structure with compact labels and selected evidence
- dense: rich poster, but still clean; more section labels, more evidence cards, more annotated structure, never paragraph-heavy
Current mode: {text_density_mode}

Beauty requirements:
- make it look expensive, precise, and publication-ready
- avoid flat generic template appearance
- use hierarchy, rhythm, spacing, and focal contrast to create visual appeal
- create a refined “conference poster / research magazine infographic” feeling
- elegant, intelligent, and credible

Negative constraints:
- no advertising style
- no stock-photo layout
- no random 3D objects
- no chaotic collage
- no excessive empty background
- no irrelevant scientific imagery
- no copied source figure
- no flashy decoration
- no cartoon style
- no overly plain template look
- no speculative charts unsupported by the brief

Final quality order:
1. scientific faithfulness
2. information hierarchy
3. visual sophistication
4. readability
5. compact richness

Render one final poster only.
"""


class PipelineError(RuntimeError):
    """Structured pipeline error."""


@dataclass
class ImageReference:
    index: int
    url: str
    alt: str = ""
    title: str = ""


@dataclass
class ArticleContext:
    title: str
    markdown: str
    image_references: list[ImageReference]


@dataclass
class ImageGenerationResult:
    image_bytes: bytes
    mime_type: str
    source: str


def log_step(step: str, message: str) -> None:
    print(f"[{step}] {message}", flush=True)


def truncate_text(text: str, max_length: int = DEFAULT_MAX_CONTEXT_CHARS) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_period = max(
        truncated.rfind("。"),
        truncated.rfind("."),
        truncated.rfind("！"),
        truncated.rfind("!"),
        truncated.rfind("？"),
        truncated.rfind("?"),
    )
    if last_period > max_length * 0.8:
        return truncated[: last_period + 1]
    return truncated


def infer_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


def extract_image_references(markdown: str) -> list[ImageReference]:
    refs: list[ImageReference] = []
    seen: set[str] = set()

    for match in MARKDOWN_IMAGE_RE.finditer(markdown):
        url = match.group("url").strip()
        if url in seen:
            continue
        seen.add(url)
        refs.append(
            ImageReference(
                index=len(refs) + 1,
                url=url,
                alt=(match.group("alt") or "").strip(),
                title=(match.group("title") or "").strip(),
            )
        )

    for match in HTML_IMAGE_RE.finditer(markdown):
        url = match.group("url").strip()
        if url in seen:
            continue
        seen.add(url)
        refs.append(
            ImageReference(
                index=len(refs) + 1,
                url=url,
                alt=(match.group("alt") or "").strip(),
                title="",
            )
        )

    return refs


def load_article_context(paper_path: Path) -> ArticleContext:
    if not paper_path.exists():
        raise PipelineError(f"Markdown 文件不存在: {paper_path}")

    markdown = paper_path.read_text(encoding="utf-8")
    if not markdown.strip():
        raise PipelineError(f"Markdown 文件为空: {paper_path}")

    title = infer_title(markdown, paper_path.stem)
    refs = extract_image_references(markdown)
    return ArticleContext(title=title, markdown=markdown, image_references=refs)


def format_image_references(refs: list[ImageReference]) -> str:
    if not refs:
        return "无图片参考。"
    blocks = []
    for ref in refs:
        blocks.append(
            "\n".join(
                [
                    f"图 {ref.index}",
                    f"URL: {ref.url}",
                    f"alt: {ref.alt or '无'}",
                    f"title: {ref.title or '无'}",
                ]
            )
        )
    return "\n\n".join(blocks)


def build_visual_summary_prompt(article: ArticleContext) -> str:
    return DEFAULT_IMAGE_SUMMARY_PROMPT.format(
        title=article.title,
        context=truncate_text(article.markdown),
    )


def build_image_prompt(
    title: str,
    visual_summary: str,
    aspect_ratio: str,
    text_density_mode: str,
) -> str:
    return DEFAULT_IMAGE_GENERATION_PROMPT.format(
        summary_for_image=visual_summary.strip(),
        title=title,
        aspect_ratio=aspect_ratio,
        text_density_mode=text_density_mode,
    )


def normalize_endpoint(base_url: str, default_path: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise PipelineError("API 地址不能为空")

    parsed = urllib.parse.urlparse(base)
    if not parsed.scheme or not parsed.netloc:
        raise PipelineError(f"API 地址格式无效: {base_url}")

    if parsed.path.endswith(default_path):
        return base
    if parsed.path.endswith("/v1"):
        return f"{base}{default_path[len('/v1'):]}"
    if parsed.path and parsed.path != "/":
        return base
    return f"{base}{default_path}"


def request_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int = 300,
) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=body, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(
            f"HTTP {exc.code} 调用失败: {url}\n响应内容:\n{error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"网络请求失败: {url}\n原因: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            f"接口未返回有效 JSON: {url}\n响应片段:\n{raw[:1000]}"
        ) from exc


def request_json_with_curl(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int = 300,
) -> Any:
    cmd = [
        "curl",
        "-sS",
        "--max-time",
        str(timeout),
        "-X",
        "POST",
        url,
        "-H",
        "Content-Type: application/json",
    ]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.extend(["-d", json.dumps(payload, ensure_ascii=False)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineError(
            f"curl 调用失败: {url}\n退出码: {result.returncode}\n错误输出:\n{result.stderr[:1000]}"
        )

    raw = result.stdout.strip()
    if not raw:
        raise PipelineError(f"curl 未返回内容: {url}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            f"curl 返回内容不是有效 JSON: {url}\n响应片段:\n{raw[:1000]}"
        ) from exc


def download_binary(url: str, timeout: int = 300) -> tuple[bytes, str]:
    req = urllib.request.Request(url=url, method="GET")
    req.add_header("Accept", "image/*,*/*;q=0.8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            mime = response.headers.get_content_type() or guess_mime_type(url)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(
            f"下载图片失败 HTTP {exc.code}: {url}\n响应内容:\n{error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"下载图片失败: {url}\n原因: {exc}") from exc
    return data, mime


def extract_text_from_chat_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text" and isinstance(part.get("text"), str) or part.get("type") == "output_text" and isinstance(
                part.get("text"), str
            ):
                texts.append(part["text"])
            elif isinstance(part.get("content"), str):
                texts.append(part["content"])
        return "\n".join(texts).strip()
    return ""


def extract_data_url_base64(text: str) -> tuple[str, str]:
    """
    Extract (mime, base64_data) from patterns like:
    ![image](data:image/png;base64,AAA...)
    or raw: data:image/png;base64,AAA...
    """
    m = re.search(
        r"data:(image\/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\n\r\s]+)",
        text,
    )
    if not m:
        raise ValueError("No data:image/...;base64,... found in response text")
    mime = m.group(1).strip()
    b64 = m.group(2).strip()
    b64 = re.sub(r"\s+", "", b64)
    return mime, b64


def decode_base64_bytes(b64: str) -> bytes:
    clean = re.sub(r"\s+", "", b64)
    if not clean:
        raise PipelineError("base64 数据为空")

    missing_padding = len(clean) % 4
    if missing_padding:
        clean += "=" * (4 - missing_padding)

    try:
        return base64.b64decode(clean, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PipelineError(f"base64 解码失败: {exc}") from exc


def try_extract_image_result_from_text(
    text: str, source: str
) -> ImageGenerationResult | None:
    if not text:
        return None

    try:
        mime, b64 = extract_data_url_base64(text)
        return ImageGenerationResult(
            image_bytes=decode_base64_bytes(b64),
            mime_type=mime,
            source=source,
        )
    except ValueError:
        pass

    urls = HTTP_URL_RE.findall(text)
    if urls:
        image_bytes, mime_type = download_binary(urls[0])
        return ImageGenerationResult(
            image_bytes=image_bytes,
            mime_type=mime_type,
            source=urls[0],
        )

    return None


def iter_all_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
        return
    if isinstance(obj, dict):
        for value in obj.values():
            yield from iter_all_strings(value)
        return
    if isinstance(obj, list):
        for item in obj:
            yield from iter_all_strings(item)


def call_llm_chat(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    image_urls: list[str],
    try_multimodal: bool = True,
    enable_thinking: bool = False,
) -> str:
    endpoint = normalize_endpoint(base_url, "/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}"}

    def build_payload(multimodal: bool) -> dict[str, Any]:
        if multimodal and image_urls:
            user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
            for url in image_urls[:8]:
                user_content.append({"type": "image_url", "image_url": {"url": url}})
            message_content: Any = user_content
        else:
            message_content = prompt

        return {
            "model": model,
            "temperature": 0.2,
            "enable_thinking": enable_thinking,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise research summarization assistant.",
                },
                {"role": "user", "content": message_content},
            ],
        }

    if try_multimodal and image_urls:
        try:
            response = request_json(endpoint, build_payload(multimodal=True), headers)
            text = parse_chat_completion_text(response)
            if text:
                return text
        except PipelineError as exc:
            log_step("LLM", f"多模态请求失败，回退到纯文本模式: {exc}")

    response = request_json(endpoint, build_payload(multimodal=False), headers)
    text = parse_chat_completion_text(response)
    if not text:
        raise PipelineError("LLM 未返回可用文本内容")
    return text


def parse_chat_completion_text(response: Any) -> str:
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            text = extract_text_from_chat_content(message.get("content"))
            if text:
                return text

        output = response.get("output")
        if isinstance(output, list):
            texts = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                texts.append(extract_text_from_chat_content(item.get("content")))
            joined = "\n".join(filter(None, texts)).strip()
            if joined:
                return joined
    return ""


def call_image_api(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    raw_response_dir: Path | None = None,
) -> ImageGenerationResult:
    endpoint = normalize_endpoint(base_url, "/v1/responses")
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "tools": [{"type": "image_generation"}],
    }

    # log_step("IMAGE", "直接使用 curl 通道")
    response = request_json_with_curl(endpoint, payload, headers)

    save_dir = (
        raw_response_dir if raw_response_dir is not None else Path("image_output")
    )
    raw_response_path = save_dir / "image_api_raw_response.json"
    raw_response_path.write_text(
        json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return parse_image_response(response)


def parse_image_response(response: Any) -> ImageGenerationResult:
    if not isinstance(response, dict):
        raise PipelineError("生图接口返回格式不是 JSON object")

    data = response.get("data")
    if isinstance(data, list) and data:
        item = data[0]
        if isinstance(item, dict):
            b64 = item.get("b64_json") or item.get("b64")
            if isinstance(b64, str) and b64.strip():
                return ImageGenerationResult(
                    image_bytes=decode_base64_bytes(b64),
                    mime_type="image/png",
                    source="b64_json",
                )
            url = item.get("url")
            if isinstance(url, str) and url.strip():
                image_bytes, mime_type = download_binary(url.strip())
                return ImageGenerationResult(
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    source=url.strip(),
                )

    candidates = response.get("candidates")
    if isinstance(candidates, list) and candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if isinstance(parts, list):
            for part in parts:
                if not isinstance(part, dict):
                    continue
                inline = part.get("inlineData") or part.get("inline_data")
                if isinstance(inline, dict) and inline.get("data"):
                    return ImageGenerationResult(
                        image_bytes=decode_base64_bytes(str(inline["data"])),
                        mime_type=inline.get("mimeType", "image/png"),
                        source="gemini-inlineData",
                    )

    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue

            if item.get("type") == "image_generation_call":
                result = item.get("result")
                if isinstance(result, str) and result.strip():
                    parsed = try_extract_image_result_from_text(
                        result,
                        source=item.get("id", "image_generation_call"),
                    )
                    if parsed is not None:
                        return parsed
                    return ImageGenerationResult(
                        image_bytes=decode_base64_bytes(result),
                        mime_type="image/png",
                        source=item.get("id", "image_generation_call"),
                    )

            text = extract_text_from_chat_content(item.get("content"))
            parsed = try_extract_image_result_from_text(
                text,
                source=response.get("id", "responses-output"),
            )
            if parsed is not None:
                return parsed

    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        text = extract_text_from_chat_content(content)
        parsed = try_extract_image_result_from_text(text, source="choices-message")
        if parsed is not None:
            return parsed

    for text in iter_all_strings(response):
        parsed = try_extract_image_result_from_text(
            text,
            source=response.get("id", "response-string-scan"),
        )
        if parsed is not None:
            return parsed

    raise PipelineError(
        "生图接口响应中未识别到图片数据。请检查 image_api_raw_response.json，重点看 data / candidates / output / choices。"
    )


def extract_http_urls_from_content(content: Any) -> list[str]:
    text = extract_text_from_chat_content(content)
    return HTTP_URL_RE.findall(text)


def guess_mime_type(url: str) -> str:
    guessed = mimetypes.guess_type(url)[0]
    return guessed or "image/png"


def suffix_for_mime(mime_type: str) -> str:
    ext = mimetypes.guess_extension(mime_type) or ".png"
    if ext == ".jpe":
        return ".jpg"
    return ext


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_binary(path: Path, content: bytes) -> None:
    path.write_bytes(content)


def build_manifest(
    article: ArticleContext,
    args: argparse.Namespace,
    summary_path: Path,
    prompt_path: Path,
    image_path: Path,
    image_result: ImageGenerationResult,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "paper_path": str(Path(args.paper).resolve()),
        "title": article.title,
        "llm_base_url": args.llm_base_url,
        "image_base_url": args.image_base_url,
        "llm_model": args.llm_model,
        "image_model": args.image_model,
        "image_reference_count": len(article.image_references),
        "image_references": [asdict(ref) for ref in article.image_references],
        "outputs": {
            "visual_summary": str(summary_path.resolve()),
            "image_prompt": str(prompt_path.resolve()),
            "poster_image": str(image_path.resolve()),
        },
        "image_result": {
            "mime_type": image_result.mime_type,
            "source": image_result.source,
            "bytes": len(image_result.image_bytes),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a one-image summary poster from paper.md"
    )
    parser.add_argument("--paper", default=DEFAULT_PAPER_PATH, help="Markdown path")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for summary, prompt, image, and manifest",
    )
    parser.add_argument("--llm-base-url", default=DEFAULT_LLM_BASE_URL)
    parser.add_argument("--image-base-url", default=DEFAULT_IMAGE_BASE_URL)
    parser.add_argument("--llm-api-key", default=DEFAULT_LLM_API_KEY)
    parser.add_argument("--image-api-key", default=DEFAULT_IMAGE_API_KEY)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--image-model", default=DEFAULT_IMAGE_MODEL)
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO)
    parser.add_argument(
        "--text-density-mode",
        default=DEFAULT_TEXT_DENSITY_MODE,
        choices=["sparse", "balanced", "dense"],
    )
    parser.add_argument(
        "--disable-thinking",
        action="store_false",
        dest="enable_thinking",
        help="Pass enable_thinking=false to the LLM API",
    )
    parser.add_argument(
        "--disable-multimodal-llm",
        action="store_true",
        help="Do not send image_url parts to the LLM stage",
    )
    parser.set_defaults(enable_thinking=LLM_ENABLE_THINKING)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        paper_path = Path(args.paper)
        output_dir = ensure_output_dir(Path(args.output_dir))

        # log_step("1/5", f"读取文章: {paper_path}")
        article = load_article_context(paper_path)
        # log_step(
        #     "1/5",
        #     f"标题: {article.title}，检测到 {len(article.image_references)} 张图片引用",
        # )

        # log_step("2/5", "生成视觉摘要提示词")
        visual_summary_prompt = build_visual_summary_prompt(article)

        requested_image_path = output_dir / "poster.png"

        # log_step("3/5", "调用 LLM 生成视觉摘要")
        visual_summary = call_llm_chat(
            base_url=args.llm_base_url,
            api_key=args.llm_api_key,
            model=args.llm_model,
            prompt=visual_summary_prompt,
            image_urls=[ref.url for ref in article.image_references],
            try_multimodal=not args.disable_multimodal_llm,
            enable_thinking=args.enable_thinking,
        )

        # log_step("4/5", "构建生图提示词并调用生图接口")
        image_prompt = build_image_prompt(
            title=article.title,
            visual_summary=visual_summary,
            aspect_ratio=args.aspect_ratio,
            text_density_mode=args.text_density_mode,
        )

        # write_text(summary_path, visual_summary.strip() + "\n")
        # write_text(prompt_path, image_prompt.strip() + "\n")

        image_result = call_image_api(
            base_url=args.image_base_url,
            api_key=args.image_api_key,
            model=args.image_model,
            prompt=image_prompt,
            raw_response_dir=output_dir,
        )

        final_image_path = requested_image_path.with_suffix(
            suffix_for_mime(image_result.mime_type)
        )
        write_binary(final_image_path, image_result.image_bytes)

        # manifest = build_manifest(
        #     article=article,
        #     args=args,
        #     summary_path=summary_path,
        #     prompt_path=prompt_path,
        #     image_path=final_image_path,
        #     image_result=image_result,
        # )
        # write_text(
        #     manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        # )

        # log_step("5/5", f"视觉摘要已保存: {summary_path}")
        # log_step("5/5", f"生图提示词已保存: {prompt_path}")
        # log_step("5/5", f"海报图片已保存: {final_image_path}")
        # log_step("5/5", f"清单已保存: {manifest_path}")
        log_step(
            "DONE",
            f"mime={image_result.mime_type}, bytes={len(image_result.image_bytes)}, source={image_result.source}",
        )
        return 0
    except KeyboardInterrupt:
        log_step("ERROR", "用户中断执行")
        return 130
    except Exception as exc:
        log_step("ERROR", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
