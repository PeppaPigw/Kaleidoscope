"""Shared utilities for LLM-powered services.

Provides robust JSON parsing, repair, and common patterns used across
all research intelligence services.
"""

import json
import re
from typing import Any


def parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM output with aggressive repair for truncation.

    Handles: markdown code blocks, preamble text, truncated JSON,
    unbalanced brackets, trailing commas, and partial responses.
    """
    if not text:
        return {}

    text = text.strip()

    # Strip markdown code blocks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()

    # Find JSON start
    if not text.startswith("{"):
        start = text.find("{")
        if start >= 0:
            text = text[start:]
        else:
            return {}

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding the last complete JSON object
    end = text.rfind("}")
    if end > 0:
        try:
            return json.loads(text[:end + 1])
        except json.JSONDecodeError:
            pass

    # Aggressive repair: remove trailing comma, close brackets
    repaired = text.rstrip()
    # Remove trailing comma before we close
    if repaired.endswith(","):
        repaired = repaired[:-1]

    # Remove incomplete key-value pairs at the end
    # Pattern: trailing "key": or "key": "incomplete
    incomplete_kv = re.search(r',\s*"[^"]*":\s*(?:"[^"]*)?$', repaired)
    if incomplete_kv:
        repaired = repaired[:incomplete_kv.start()]

    # Remove incomplete array items
    incomplete_arr = re.search(r',\s*(?:\{[^}]*|"[^"]*)$', repaired)
    if incomplete_arr and repaired.count('{') > repaired.count('}'):
        repaired = repaired[:incomplete_arr.start()]

    # Close unbalanced brackets
    open_braces = repaired.count('{') - repaired.count('}')
    open_brackets = repaired.count('[') - repaired.count(']')

    # Remove trailing comma again after trimming
    repaired = repaired.rstrip().rstrip(',')

    repaired += ']' * max(0, open_brackets) + '}' * max(0, open_braces)

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Last resort: find the largest valid JSON substring
    for end_pos in range(len(text) - 1, 0, -1):
        if text[end_pos] == '}':
            try:
                return json.loads(text[:end_pos + 1])
            except json.JSONDecodeError:
                continue

    return {}


def truncate_for_prompt(text: str, max_chars: int = 200) -> str:
    """Truncate text for use in prompts, preserving word boundaries."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    return truncated + "..."


def format_claims_for_prompt(claims: list, max_items: int = 10, max_chars: int = 150) -> str:
    """Format a list of claims for inclusion in a prompt."""
    lines = []
    for c in claims[:max_items]:
        if isinstance(c, dict):
            text = c.get("text", c.get("claim", c.get("title", str(c))))
        else:
            text = str(c)
        lines.append(f"- {text[:max_chars]}")
    return "\n".join(lines) or "No claims available"


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def llm_complete_json(
    prompt: str,
    system: str,
    *,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retry_prompt: str | None = None,
) -> dict:
    """Complete an LLM call and parse JSON, with automatic retry on empty/truncated response.

    If the first attempt returns empty or unparseable JSON and retry_prompt is provided,
    retries with the shorter prompt.
    """
    from app.clients.llm_client import LLMClient

    llm = LLMClient()
    raw = await llm.complete(
        prompt=prompt,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    data = parse_llm_json(raw)

    if not data and retry_prompt:
        raw = await llm.complete(
            prompt=retry_prompt,
            system="Output valid JSON only. No markdown.",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        data = parse_llm_json(raw)

    return data
