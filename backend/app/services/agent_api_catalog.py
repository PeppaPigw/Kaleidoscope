"""Agent-native research API catalog loaded from the roadmap memo."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class AgentApiSpec:
    """One planned agent API endpoint from docs/memo/Agent-API.md."""

    id: str
    method: str
    path: str
    priority: str
    use_case: str
    response_highlights: tuple[str, ...]
    section: str
    tag: str

    @property
    def path_params(self) -> tuple[str, ...]:
        return tuple(re.findall(r"\{([^}]+)\}", self.path))

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def operation_id(self) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", self.path.strip("/"))
        return f"agent_{self.id.lower()}_{self.method.lower()}_{slug}".strip("_")


_ROW_RE = re.compile(
    r"^\|\s*(?P<id>[A-Z][0-9]{2})\s*\|\s*`\[ \]\s*"
    r"(?P<method>GET|POST|PUT|PATCH|DELETE)\s+(?P<path>[^`]+)`\s*\|\s*"
    r"(?P<priority>P[0-9])\s*\|\s*(?P<use_case>.*?)\s*\|\s*"
    r"(?P<highlights>.*?)\s*\|\s*$"
)
_SECTION_RE = re.compile(r"^###\s+(?P<letter>[A-Z])\.\s+(?P<title>.+?)\s*$")
_CODE_RE = re.compile(r"`([^`]+)`")

_TAG_BY_SECTION_LETTER = {
    "A": "agent-acquisition",
    "B": "agent-paper-access",
    "C": "agent-visual-artifacts",
    "D": "agent-scientific-extraction",
    "E": "agent-external-artifacts",
    "F": "agent-citation-intelligence",
    "G": "agent-topic-intelligence",
    "H": "agent-synthesis-planning",
    "I": "agent-reproducibility-quality",
    "J": "agent-orchestration",
    "K": "agent-research-output",
    "L": "agent-monitoring-memory",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _roadmap_path() -> Path:
    return _repo_root() / "docs" / "memo" / "Agent-API.md"


def _parse_highlights(value: str) -> tuple[str, ...]:
    fields: list[str] = []
    for raw in _CODE_RE.findall(value):
        for part in raw.split(","):
            field = part.strip()
            if not field:
                continue
            fields.append(field)
    return tuple(dict.fromkeys(fields))


@lru_cache(maxsize=1)
def load_agent_api_specs() -> tuple[AgentApiSpec, ...]:
    """Load endpoint specs from the memo so docs and runtime stay in sync."""

    path = _roadmap_path()
    current_section = "Agent APIs"
    current_tag = "agent-research"
    specs: list[AgentApiSpec] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            letter = section_match.group("letter")
            current_section = section_match.group("title")
            current_tag = _TAG_BY_SECTION_LETTER.get(letter, "agent-research")
            continue

        row_match = _ROW_RE.match(line)
        if not row_match:
            continue

        specs.append(
            AgentApiSpec(
                id=row_match.group("id"),
                method=row_match.group("method"),
                path=row_match.group("path").strip(),
                priority=row_match.group("priority"),
                use_case=row_match.group("use_case").strip(),
                response_highlights=_parse_highlights(row_match.group("highlights")),
                section=current_section,
                tag=current_tag,
            )
        )

    return tuple(specs)
