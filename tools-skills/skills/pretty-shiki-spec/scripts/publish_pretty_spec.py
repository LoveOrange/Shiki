#!/usr/bin/env python3
"""Publish Shiki L1 specs as a human-friendly L0 HTML specification."""

import argparse
import html
import importlib.util
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


PRETTY_SITE_CSS = """
:root {
  --bg: #f4f1ea;
  --paper: #fffdfa;
  --paper-strong: #ffffff;
  --ink: #20252f;
  --muted: #667085;
  --soft: #8a94a6;
  --line: #ddd6c8;
  --line-soft: #eee7dc;
  --nav: #18212f;
  --nav-ink: #f8fafc;
  --nav-muted: #b7c0cf;
  --teal: #0f766e;
  --teal-soft: #dff3ee;
  --teal-line: #7bc3b5;
  --amber: #a35c00;
  --amber-soft: #fff2d5;
  --rose: #b42318;
  --rose-soft: #ffe4df;
  --code: #111827;
  --code-line: #273142;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    linear-gradient(180deg, rgb(255 255 255 / 72%) 0%, rgb(244 241 234 / 88%) 38%, var(--bg) 100%);
  color: var(--ink);
  font: 15px/1.7 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--teal); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr) minmax(220px, 280px);
  min-height: 100vh;
}
.view-controls {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 40;
  display: flex;
  gap: 5px;
  align-items: center;
  border: 1px solid rgb(32 37 47 / 12%);
  border-radius: 8px;
  background: rgb(255 253 250 / 92%);
  box-shadow: 0 12px 28px rgb(32 37 47 / 14%);
  padding: 5px;
  backdrop-filter: blur(10px);
}
.view-controls button {
  min-width: 44px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: #344054;
  cursor: pointer;
  font-size: 12px;
  font-weight: 750;
  line-height: 1;
  padding: 8px 9px;
}
.view-controls button:hover { background: #f2ece1; }
.view-controls button.active {
  border-color: var(--teal-line);
  background: var(--teal-soft);
  color: #0a4f49;
}
.view-controls button:focus-visible {
  outline: 2px solid var(--teal-line);
  outline-offset: 2px;
}
body.nav-collapsed:not(.toc-collapsed):not(.focus-mode) .layout {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
}
body.toc-collapsed:not(.nav-collapsed):not(.focus-mode) .layout {
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
}
body.nav-collapsed.toc-collapsed .layout,
body.focus-mode .layout {
  grid-template-columns: minmax(0, 1fr);
}
body.nav-collapsed .sidebar,
body.focus-mode .sidebar,
body.toc-collapsed .toc-panel,
body.focus-mode .toc-panel {
  display: none;
}
body.focus-mode article,
body.focus-mode .source {
  width: min(100%, 1080px);
}
.sidebar {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow: auto;
  border-right: 1px solid rgb(255 255 255 / 12%);
  background: linear-gradient(180deg, #202b3c 0%, var(--nav) 100%);
  color: var(--nav-ink);
  padding: 24px 14px 28px;
}
.brand {
  display: flex;
  gap: 11px;
  align-items: center;
  margin: 0 8px 7px;
  color: var(--nav-ink);
  font-size: 18px;
  line-height: 1.25;
  font-weight: 800;
}
.brand::before {
  content: "";
  width: 10px;
  height: 30px;
  border-radius: 4px;
  background: linear-gradient(180deg, #48b8a7, #f0a437 58%, #d1493f);
  flex: 0 0 auto;
}
.generated {
  margin: 0 8px 18px;
  color: var(--nav-muted);
  font-size: 12px;
}
.nav-tree {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.nav-group { margin-top: 2px; }
.nav-group summary {
  display: flex;
  gap: 8px;
  align-items: baseline;
  justify-content: space-between;
  cursor: pointer;
  list-style: none;
  border-radius: 7px;
  color: var(--nav-ink);
  font-size: 13px;
  font-weight: 760;
  padding: 8px 9px;
  overflow-wrap: anywhere;
}
.nav-group summary::-webkit-details-marker { display: none; }
.nav-group summary:hover { background: rgb(255 255 255 / 8%); }
.nav-group summary::before {
  content: "+";
  color: #90d2c8;
  flex: 0 0 auto;
  font-weight: 800;
}
.nav-group[open] > summary::before { content: "-"; }
.nav-folder-name {
  flex: 1 1 auto;
  min-width: 0;
}
.nav-count {
  color: var(--nav-muted);
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 650;
}
.nav-group-pages {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 14px;
  padding: 2px 0 7px 9px;
  border-left: 1px solid rgb(255 255 255 / 12%);
}
.nav-root-pages {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: block;
  padding: 8px 9px;
  border-radius: 7px;
  color: var(--nav-ink);
}
.nav-item:hover {
  background: rgb(255 255 255 / 8%);
  text-decoration: none;
}
.nav-item.active {
  background: rgb(223 243 238 / 14%);
  box-shadow: inset 3px 0 0 #48b8a7;
}
.nav-item span {
  display: block;
  overflow-wrap: anywhere;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.25;
}
.nav-item small {
  display: block;
  color: var(--nav-muted);
  overflow-wrap: anywhere;
  font-size: 11px;
  line-height: 1.25;
  margin-top: 2px;
}
.content {
  min-width: 0;
  padding: 36px 46px 76px;
}
.source {
  width: min(100%, 1120px);
  margin: 0 auto 14px;
  color: var(--muted);
  font-size: 12px;
}
.source code {
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff8ee;
  color: #6d3b00;
  padding: 2px 5px;
}
article {
  width: min(100%, 1120px);
  margin: 0 auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  box-shadow: 0 18px 48px rgb(32 37 47 / 10%);
  overflow-wrap: break-word;
  padding: clamp(24px, 4vw, 48px);
}
article > *:first-child { margin-top: 0; }
article h1 {
  margin: 0 0 16px;
  color: #151a23;
  font-size: clamp(30px, 4vw, 48px);
  line-height: 1.08;
  letter-spacing: 0;
}
article h2 {
  margin: 36px 0 13px;
  padding-top: 18px;
  border-top: 1px solid var(--line-soft);
  color: #18212f;
  font-size: 22px;
  line-height: 1.22;
  letter-spacing: 0;
}
article h3 {
  margin: 24px 0 10px;
  color: #243047;
  font-size: 17px;
  line-height: 1.3;
  letter-spacing: 0;
}
article h4 {
  margin: 18px 0 8px;
  color: #384152;
  font-size: 14px;
  line-height: 1.35;
  letter-spacing: 0;
  text-transform: uppercase;
}
.anchor {
  display: inline-block;
  width: 0;
  margin-left: -18px;
  padding-right: 18px;
  color: var(--soft);
  opacity: 0;
}
h1:hover .anchor,
h2:hover .anchor,
h3:hover .anchor,
h4:hover .anchor { opacity: 1; text-decoration: none; }
p { margin: 10px 0 14px; }
blockquote {
  margin: 18px 0;
  border-left: 4px solid var(--teal-line);
  border-radius: 0 7px 7px 0;
  background: var(--teal-soft);
  color: #26413e;
  padding: 12px 16px;
}
ul,
ol {
  margin: 10px 0 18px;
  padding-left: 25px;
}
li { margin: 5px 0; }
hr {
  margin: 28px 0;
  border: 0;
  border-top: 1px solid var(--line);
}
table {
  width: 100%;
  max-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 16px 0 24px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper-strong);
  table-layout: fixed;
}
.table-scroll {
  width: 100%;
  max-width: 100%;
  margin: 16px 0 24px;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper-strong);
}
.table-scroll table {
  width: max-content;
  min-width: 100%;
  max-width: none;
  margin: 0;
  overflow: visible;
  border: 0;
  border-radius: 0;
  table-layout: auto;
}
th,
td {
  border-bottom: 1px solid var(--line-soft);
  border-right: 1px solid var(--line-soft);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
  word-break: normal;
}
.table-scroll th,
.table-scroll td {
  min-width: 136px;
  max-width: 360px;
}
.table-scroll th:first-child,
.table-scroll td:first-child {
  min-width: 112px;
}
th:last-child,
td:last-child { border-right: 0; }
tr:last-child td { border-bottom: 0; }
th {
  background: #f6efe4;
  color: #303746;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  line-height: 1.35;
  text-transform: uppercase;
}
td { color: #333b4b; }
th a,
td a,
th code,
td code {
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
}
td:first-child code,
td:nth-child(2) code {
  color: #0a4f49;
  font-weight: 700;
}
code {
  border-radius: 5px;
  background: #f0eadf;
  color: #613b00;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .92em;
  padding: .12em .34em;
}
pre {
  position: relative;
  margin: 16px 0 24px;
  overflow: auto;
  border: 1px solid #263244;
  border-radius: 8px;
  background: var(--code);
  color: #e5e7eb;
}
pre code {
  display: block;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 13px;
  line-height: 1.6;
  padding: 16px;
}
.code-copy {
  position: absolute;
  top: 8px;
  right: 8px;
  border: 1px solid rgb(255 255 255 / 18%);
  border-radius: 6px;
  background: rgb(255 255 255 / 10%);
  color: #f8fafc;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  padding: 5px 8px;
}
.diagram {
  margin: 18px 0 26px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fffaf2;
  overflow: hidden;
}
.diagram-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  border-bottom: 1px solid var(--line-soft);
  background: #f6efe4;
  padding: 8px;
}
.diagram-toolbar button {
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fffdfa;
  color: #344054;
  cursor: pointer;
  font-size: 12px;
  font-weight: 750;
  padding: 6px 8px;
}
.diagram-toolbar button:hover {
  border-color: var(--teal-line);
  background: var(--teal-soft);
}
.diagram-canvas {
  min-height: 220px;
  overflow: auto;
  padding: 18px;
}
.diagram-source {
  border-top: 1px solid var(--line-soft);
  padding: 0 12px 12px;
}
.diagram-source summary {
  cursor: pointer;
  color: var(--muted);
  font-weight: 700;
  padding: 10px 0;
}
.toc-panel {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow: auto;
  border-left: 1px solid var(--line);
  background: rgb(255 253 250 / 78%);
  padding: 76px 20px 28px;
}
.toc-title {
  margin-bottom: 10px;
  color: #344054;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}
.toc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toc-item {
  border-radius: 6px;
  color: #526071;
  font-size: 13px;
  line-height: 1.3;
  padding: 6px 8px;
}
.toc-item:hover {
  background: #f2ece1;
  color: #20252f;
  text-decoration: none;
}
.toc-level-2 { padding-left: 18px; }
.toc-level-3 { padding-left: 30px; }
.toc-level-4 { padding-left: 42px; font-size: 12px; }
.toc-empty {
  color: var(--muted);
  font-size: 13px;
}
.landing-main {
  width: min(100%, 1120px);
  margin: 0 auto;
  padding: 46px 34px 72px;
}
.landing-main h1 {
  margin: 0 0 12px;
  color: #151a23;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.05;
  letter-spacing: 0;
}
.landing-section {
  margin-top: 26px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  padding: 18px;
}
.landing-section h2 {
  display: flex;
  gap: 12px;
  align-items: baseline;
  justify-content: space-between;
  margin: 0 0 12px;
  color: #20252f;
  font-size: 18px;
  letter-spacing: 0;
}
.landing-section h2 small {
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
}
.landing-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 8px;
}
.landing-list .nav-item {
  border: 1px solid var(--line-soft);
  background: #fffdfa;
  color: #20252f;
}
.landing-list .nav-item small {
  color: var(--muted);
}
@media (max-width: 1040px) {
  .layout { grid-template-columns: minmax(250px, 310px) minmax(0, 1fr); }
  .toc-panel { display: none; }
  .content { padding: 32px 28px 64px; }
}
@media (max-width: 760px) {
  .layout { display: block; }
  .sidebar {
    position: static;
    height: auto;
    max-height: 52vh;
    border-right: 0;
    border-bottom: 1px solid rgb(255 255 255 / 14%);
  }
  .view-controls { display: none; }
  .content { padding: 24px 14px 52px; }
  article { padding: 22px 16px; }
  th, td { min-width: 0; }
}
"""


PLACEHOLDER_RE = re.compile(r"\bTBD\b|\[TBD\]|\[___\]|\[ \]|\?\?\?|TODO", re.I)
GENERATED_SOURCE_DIR = "_l0_source"


@dataclass
class SourceRef:
    role: str
    path: Path
    exists: bool = True


@dataclass
class FeatureSpec:
    feature_id: str
    path: Path
    docs: dict[str, Path] = field(default_factory=dict)
    plan_items: list[dict[str, str]] = field(default_factory=list)
    plan_meta: dict[str, str] = field(default_factory=dict)
    design_docs: list[Path] = field(default_factory=list)
    missing_targets: list[str] = field(default_factory=list)
    placeholders: list[tuple[Path, int, str]] = field(default_factory=list)


@dataclass
class ContextModel:
    input_path: Path
    context_dir: Path
    project_dir: Path | None
    feature_specs: list[FeatureSpec]
    module_dirs: list[Path]
    source_refs: list[SourceRef]
    placeholders: list[tuple[Path, int, str]]
    generated_at: str


def find_project_root() -> Path:
    return Path.cwd().resolve()


def resolve_path(raw: str | None, project_root: Path) -> Path:
    if not raw:
        candidate = project_root / "shiki_context"
        return candidate.resolve() if candidate.exists() else project_root
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def pretty_spec_dir(root: Path) -> Path:
    if root.name == "pretty_shiki_spec":
        return root
    return root / "pretty_shiki_spec"


def find_context_dir(input_path: Path) -> Path:
    start = input_path if input_path.is_dir() else input_path.parent
    candidates = [start, *start.parents]
    for candidate in candidates:
        if candidate.name == "shiki_context":
            return candidate
        child = candidate / "shiki_context"
        if child.is_dir():
            return child
    return start


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_cell(value: str) -> str:
    value = value.strip()
    value = value.replace("<br>", " ").replace("<br/>", " ")
    return value.strip().strip("`").strip()


def safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", "<br>")
    text = text.replace("|", "&#124;")
    return text


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        rows = [["" for _ in headers]]
    output = [
        "| " + " | ".join(safe_cell(header) for header in headers) + " |",
        "|" + "|".join(":---" for _ in headers) + "|",
    ]
    for row in rows:
        padded = list(row) + [""] * max(0, len(headers) - len(row))
        output.append("| " + " | ".join(safe_cell(cell) for cell in padded[: len(headers)]) + " |")
    return "\n".join(output)


def title_from_markdown(path: Path) -> str:
    if not path.exists():
        return path.stem.replace("_", " ").replace("-", " ").title()
    for line in read_text(path).splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).replace("`", "").strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def relative_to(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return str(path)


def source_code(path: Path, ctx: Path) -> str:
    return f"`{relative_to(path, ctx)}`"


def metadata_value(text: str, key: str) -> str:
    bullet_pattern = r"^\s*-\s+\*\*" + re.escape(key) + r"\*\*:\s*(.*?)\s*$"
    match = re.search(bullet_pattern, text, re.M)
    if match:
        return match.group(1).strip()
    inline_pattern = r"\*\*" + re.escape(key) + r"\*\*:\s*(.*?)(?=\s+\*\*|\s*$)"
    match = re.search(inline_pattern, text, re.M)
    return match.group(1).strip() if match else ""


def extract_section(text: str, heading_needle: str) -> str:
    lines = text.splitlines()
    start = None
    level = None
    for index, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.*)$", line)
        if match and heading_needle.lower() in match.group(2).lower():
            start = index + 1
            level = len(match.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#+)\s+", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def parse_table(section_text: str) -> list[dict[str, str]]:
    lines = [line.rstrip() for line in section_text.splitlines()]
    table_start = None
    for index in range(len(lines) - 1):
        if lines[index].strip().startswith("|") and lines[index + 1].strip().startswith("|"):
            table_start = index
            break
    if table_start is None:
        return []
    table_lines = []
    for line in lines[table_start:]:
        if not line.strip() or not line.strip().startswith("|"):
            break
        table_lines.append(line.strip())
    if len(table_lines) < 2:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        cells.extend([""] * max(0, len(headers) - len(cells)))
        rows.append({header: cells[index] for index, header in enumerate(headers)})
    return rows


def parse_plan(plan_path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    if not plan_path.exists():
        return {}, []
    text = read_text(plan_path)
    meta = {
        "Feature ID": metadata_value(text, "Feature ID"),
        "Base Module": metadata_value(text, "Base Module"),
        "Spec Revision": metadata_value(text, "Spec Revision"),
        "Contract Version": metadata_value(text, "Contract Version"),
        "Created": metadata_value(text, "Created"),
    }
    legacy_heading = "Target " + "Arti" + "facts"
    items = parse_table(extract_section(text, "Target Outputs") or extract_section(text, legacy_heading))
    return meta, items


def is_feature_dir(path: Path) -> bool:
    return path.is_dir() and ((path / "design_brief.md").exists() or (path / "_plan.md").exists())


def discover_feature_dirs(input_path: Path, context_dir: Path, requested_feature: str | None) -> list[Path]:
    if requested_feature:
        feature_dir = context_dir / "features" / requested_feature
        if not feature_dir.is_dir():
            raise FileNotFoundError(f"Feature not found: {feature_dir}")
        return [feature_dir]
    if is_feature_dir(input_path) and input_path.parent.name == "features":
        return [input_path]
    features_dir = context_dir / "features"
    if features_dir.is_dir():
        return sorted(path for path in features_dir.iterdir() if is_feature_dir(path))
    return []


def discover_module_dirs(input_path: Path, context_dir: Path, requested_module: str | None) -> list[Path]:
    if requested_module:
        module_dir = context_dir / "modules" / requested_module
        if not module_dir.is_dir():
            raise FileNotFoundError(f"Module not found: {module_dir}")
        return [module_dir]
    if input_path.is_dir() and input_path.parent.name == "modules":
        return [input_path]
    modules_dir = context_dir / "modules"
    if modules_dir.is_dir():
        return sorted(path for path in modules_dir.iterdir() if path.is_dir())
    return []


def feature_module_names(feature_specs: list[FeatureSpec]) -> set[str]:
    names: set[str] = set()
    for feature in feature_specs:
        base_module = clean_cell(feature.plan_meta.get("Base Module", ""))
        if base_module and base_module not in {"[TBD]", "TBD", "N/A", "-"}:
            names.add(base_module)
        brief_path = feature.docs.get("design_brief")
        if brief_path and brief_path.exists():
            brief_module = clean_cell(metadata_value(read_text(brief_path), "Module"))
            if brief_module and brief_module not in {"[optional; design_init may infer it]", "[TBD]", "TBD", "N/A", "-"}:
                names.add(brief_module)
        for item in feature.plan_items:
            target = clean_cell(item.get("target", ""))
            match = re.search(r"(?:^|/)modules/([^/]+)/", target)
            if match:
                names.add(match.group(1))
    return names


def related_module_dirs(context_dir: Path, feature_specs: list[FeatureSpec]) -> list[Path]:
    modules_root = context_dir / "modules"
    if not modules_root.is_dir():
        return []
    return sorted(
        modules_root / name
        for name in feature_module_names(feature_specs)
        if (modules_root / name).is_dir()
    )


def find_placeholders(paths: list[Path]) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in sorted(set(paths)):
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if PLACEHOLDER_RE.search(line):
                hits.append((path, line_no, line.strip()))
    return hits


def plan_target_path(feature_dir: Path, target: str) -> Path | None:
    target = clean_cell(target)
    if not target or target in {"-", "baseline", "module baseline"}:
        return None
    if "{" in target or "}" in target:
        return None
    if not target.endswith(".md"):
        return None
    return (feature_dir / target).resolve()


def collect_feature_spec(feature_dir: Path) -> FeatureSpec:
    docs = {
        "design_brief": feature_dir / "design_brief.md",
        "plan": feature_dir / "_plan.md",
        "index": feature_dir / "index.md",
        "code_contract": feature_dir / "code_contract.md",
        "test_cases": feature_dir / "tests" / "test_cases.md",
    }
    plan_meta, plan_items = parse_plan(docs["plan"])
    design_docs = []
    for root in [feature_dir / "modules"]:
        if root.is_dir():
            design_docs.extend(sorted(root.rglob("*.md")))
    expected_paths = [path for path in docs.values()]
    missing_targets = []
    for item in plan_items:
        target_path = plan_target_path(feature_dir, item.get("target", ""))
        if target_path is None:
            continue
        expected_paths.append(target_path)
        if not target_path.exists():
            missing_targets.append(relative_to(target_path, feature_dir))
    placeholders = find_placeholders(expected_paths + design_docs)
    return FeatureSpec(
        feature_id=feature_dir.name,
        path=feature_dir,
        docs=docs,
        plan_items=plan_items,
        plan_meta=plan_meta,
        design_docs=sorted(set(design_docs)),
        missing_targets=missing_targets,
        placeholders=placeholders,
    )


def collect_source_refs(context_dir: Path, feature_specs: list[FeatureSpec], module_dirs: list[Path]) -> list[SourceRef]:
    refs: list[SourceRef] = []
    project_dir = context_dir / "project"
    for name in ["index.md", "_plan.md", "architecture.md", "ubiquitous_language.md", "techstack.md", "integration.md"]:
        path = project_dir / name
        if path.exists():
            refs.append(SourceRef("project", path))
    workspace_dir = context_dir / "workspace"
    for name in ["active_task.md", "_plan.md"]:
        path = workspace_dir / name
        if path.exists():
            refs.append(SourceRef("workspace", path))
    for feature in feature_specs:
        for role, path in feature.docs.items():
            refs.append(SourceRef(f"feature:{feature.feature_id}:{role}", path, path.exists()))
        for path in feature.design_docs:
            refs.append(SourceRef(f"feature:{feature.feature_id}:leaf_spec", path))
    for module_dir in module_dirs:
        for path in sorted(module_dir.rglob("*.md")):
            refs.append(SourceRef(f"module:{module_dir.name}", path))
    unique: dict[Path, SourceRef] = {}
    for ref in refs:
        unique.setdefault(ref.path.resolve(), ref)
    return list(unique.values())


def build_context(input_path: Path, feature: str | None, module: str | None) -> ContextModel:
    context_dir = find_context_dir(input_path)
    input_is_module = input_path.is_dir() and input_path.parent.name == "modules"
    input_is_feature = is_feature_dir(input_path) and input_path.parent.name == "features"
    if (module or input_is_module) and not feature:
        feature_dirs = []
    else:
        feature_dirs = discover_feature_dirs(input_path, context_dir, feature)
    feature_specs = [collect_feature_spec(path) for path in feature_dirs]
    if module or input_is_module:
        module_dirs = discover_module_dirs(input_path, context_dir, module)
    elif feature or input_is_feature:
        module_dirs = related_module_dirs(context_dir, feature_specs)
    else:
        module_dirs = discover_module_dirs(input_path, context_dir, module)
    source_refs = collect_source_refs(context_dir, feature_specs, module_dirs)
    placeholder_paths = [ref.path for ref in source_refs if ref.exists]
    placeholders = find_placeholders(placeholder_paths)
    project_dir = context_dir / "project" if (context_dir / "project").is_dir() else None
    return ContextModel(
        input_path=input_path,
        context_dir=context_dir,
        project_dir=project_dir,
        feature_specs=feature_specs,
        module_dirs=module_dirs,
        source_refs=source_refs,
        placeholders=placeholders,
        generated_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    )


def status_for_plan_item(item: dict[str, str]) -> str:
    output_files = clean_cell(item.get("output_files", ""))
    if output_files:
        return "done"
    return "open"


def section_or_na(text: str, heading: str) -> str:
    body = extract_section(text, heading)
    if not body:
        return "- N/A"
    return body


def source_note(path: Path, context_dir: Path) -> str:
    return f"> Source L1: {source_code(path, context_dir)}"


def source_link(path: str, label: str | None = None) -> str:
    label = label or path
    return f"[{label}]({path})"


def render_readme(model: ContextModel, title: str) -> str:
    feature_count = len(model.feature_specs)
    module_count = len(model.module_dirs)
    plan_items = sum(len(feature.plan_items) for feature in model.feature_specs)
    done_items = sum(
        1
        for feature in model.feature_specs
        for item in feature.plan_items
        if status_for_plan_item(item) == "done"
    )
    missing_targets = sum(len(feature.missing_targets) for feature in model.feature_specs)
    rows = [
        ["Input", source_code(model.input_path, model.context_dir if model.context_dir.exists() else model.input_path.parent)],
        ["Features", feature_count],
        ["Modules", module_count],
        ["Plan items", plan_items],
        ["Completed plan items", done_items],
        ["Missing L1 targets", missing_targets],
        ["Open placeholders", len(model.placeholders)],
        ["Generated", model.generated_at],
    ]
    feature_rows = []
    for feature in model.feature_specs:
        overview = f"features/{feature.feature_id}/overview.md"
        base_module = feature.plan_meta.get("Base Module") or metadata_value(
            read_text(feature.docs["design_brief"]) if feature.docs["design_brief"].exists() else "",
            "Module",
        )
        feature_rows.append([
            source_link(overview, feature.feature_id),
            base_module or "N/A",
            len(feature.plan_items),
            sum(1 for item in feature.plan_items if status_for_plan_item(item) == "done"),
            len(feature.placeholders),
        ])
    module_rows = [
        [source_link(f"modules/{module_dir.name}.md", module_dir.name), source_code(module_dir, model.context_dir)]
        for module_dir in model.module_dirs
    ]
    source_rows = [
        [ref.role, source_code(ref.path, model.context_dir), "present" if ref.exists else "missing"]
        for ref in model.source_refs
    ]
    lines = [
        f"# {title}",
        "",
        "> L0 Human-Friendly Spec generated from Shiki L1 consensus specs. Edit the L1 specs, then publish again; this L0 site is a review projection, not the source of truth.",
        "",
        "## Agreement Snapshot",
        "",
        markdown_table(["item", "value"], rows),
        "",
        "## Spec Layers",
        "",
        markdown_table(
            ["layer", "purpose", "included here"],
            [
                ["L0", "Human-friendly review projection", "Overview, business view, design view, contract view, and gaps"],
                ["L1", "Consensus specs for execution", "Plans, indexes, design leaf specs, test specs, and code_contract.md"],
                ["L2", "Reusable standards and loadouts", "Tech contracts and workflow references are shown only through L1 references"],
            ],
        ),
        "",
        "## Features",
        "",
        markdown_table(["feature", "base module", "plan items", "done", "open placeholders"], feature_rows or [["N/A", "N/A", "0", "0", "0"]]),
        "",
        "## Modules",
        "",
        markdown_table(["module", "source"], module_rows or [["N/A", "N/A"]]),
        "",
        "## Review Checklist",
        "",
        "- Confirm the L0 summary matches the current business intent.",
        "- Resolve open placeholders before treating the spec as implementation-ready.",
        "- Check that each generated L0 page points back to its L1 source file.",
        "- If L0 and L1 disagree, update L1 and regenerate this site.",
        "",
        "## L1 Consensus Sources",
        "",
        markdown_table(["role", "path", "status"], source_rows or [["N/A", "N/A", "missing"]]),
        "",
        "## Gaps",
        "",
        source_link("gaps.md", "Open placeholders and missing L1 targets"),
        "",
    ]
    return "\n".join(lines)


def render_project_page(model: ContextModel) -> str:
    lines = [
        "# Project Context - Human View",
        "",
        "> L0 projection of stable project-level Shiki specs.",
        "",
    ]
    if not model.project_dir:
        lines.extend(["No `project/` specs were found.", ""])
        return "\n".join(lines)
    for filename, label, sections in [
        ("architecture.md", "Architecture", ["Overview", "Boundaries", "Modules", "Decisions"]),
        ("ubiquitous_language.md", "Ubiquitous Language", ["Terms", "Glossary", "Language"]),
        ("techstack.md", "Tech Stack", ["Stack Choices", "Runtime", "Frameworks"]),
        ("integration.md", "Integration", ["Data Sources", "External Systems", "Integrations"]),
    ]:
        path = model.project_dir / filename
        if not path.exists():
            continue
        text = read_text(path)
        lines.extend([f"## {label}", "", source_note(path, model.context_dir), ""])
        extracted = []
        for section in sections:
            body = extract_section(text, section)
            if body:
                extracted.append(body)
        if extracted:
            lines.extend(["\n\n".join(extracted), ""])
        else:
            lines.extend([short_body(text), ""])
    return "\n".join(lines)


def short_body(text: str, max_lines: int = 28) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("# "):
            continue
        lines.append(line)
        if len(lines) >= max_lines:
            lines.append("")
            lines.append("> Output shortened for L0. Read the L1 source for full detail.")
            break
    body = "\n".join(lines).strip()
    return body or "- N/A"


def render_feature_overview(feature: FeatureSpec, context_dir: Path) -> str:
    brief = read_text(feature.docs["design_brief"]) if feature.docs["design_brief"].exists() else ""
    plan_rows = []
    for item in feature.plan_items:
        plan_rows.append([
            item.get("id", ""),
            item.get("phase", ""),
            item.get("contract", ""),
            item.get("target", ""),
            item.get("depends_on", ""),
            status_for_plan_item(item),
        ])
    docs_rows = []
    for role, path in feature.docs.items():
        docs_rows.append([role, source_code(path, context_dir), "present" if path.exists() else "missing"])
    for path in feature.design_docs:
        docs_rows.append(["leaf_spec", source_code(path, context_dir), "present"])
    meta_rows = [
        ["Feature ID", feature.plan_meta.get("Feature ID") or feature.feature_id],
        ["Base Module", feature.plan_meta.get("Base Module") or metadata_value(brief, "Module") or "N/A"],
        ["Spec Revision", feature.plan_meta.get("Spec Revision") or "N/A"],
        ["Contract Version", feature.plan_meta.get("Contract Version") or "N/A"],
        ["Created", feature.plan_meta.get("Created") or metadata_value(brief, "Date") or "N/A"],
        ["Source", metadata_value(brief, "Source") or "N/A"],
    ]
    lines = [
        f"# Feature {feature.feature_id} - Human Spec",
        "",
        "> L0 overview generated from feature L1 specs. The execution contract remains `_plan.md`, leaf specs, tests, and `code_contract.md`.",
        "",
        "## Metadata",
        "",
        markdown_table(["field", "value"], meta_rows),
        "",
        "## What Is Agreed",
        "",
        source_note(feature.docs["design_brief"], context_dir) if feature.docs["design_brief"].exists() else "> Source L1: missing `design_brief.md`",
        "",
        section_or_na(brief, "Summary"),
        "",
        "## Business Rules",
        "",
        section_or_na(brief, "Business Rules"),
        "",
        "## Boundaries And Dependencies",
        "",
        section_or_na(brief, "Boundaries and Dependencies"),
        "",
        "## Delivery Plan",
        "",
        markdown_table(["id", "phase", "contract", "target", "depends_on", "status"], plan_rows or [["N/A", "N/A", "N/A", "N/A", "N/A", "open"]]),
        "",
        "## Consensus Files",
        "",
        markdown_table(["role", "path", "status"], docs_rows),
        "",
        "## Related L0 Views",
        "",
        f"- {source_link('business.md', 'Business view')}",
        f"- {source_link('design.md', 'Design view')}",
        f"- {source_link('contract.md', 'Code contract view')}",
        "",
    ]
    return "\n".join(lines)


def render_business_page(feature: FeatureSpec, context_dir: Path) -> str:
    brief_path = feature.docs["design_brief"]
    brief = read_text(brief_path) if brief_path.exists() else ""
    sections = [
        "Summary",
        "Core Concepts",
        "State Changes",
        "Operations",
        "Business Rules",
        "External Entrances and Capacity",
        "Boundaries and Dependencies",
        "Concerns and Questions",
        "References",
    ]
    lines = [
        f"# Feature {feature.feature_id} - Business View",
        "",
        source_note(brief_path, context_dir) if brief_path.exists() else "> Source L1: missing `design_brief.md`",
        "",
    ]
    for section in sections:
        lines.extend([f"## {section}", "", section_or_na(brief, section), ""])
    return "\n".join(lines)


def design_role(path: Path) -> str:
    parts = path.parts
    if "designs" in parts:
        return path.stem
    if "entrances" in parts:
        return "entrance"
    if "flows" in parts:
        return "flow"
    return path.stem


def selected_sections_for(path: Path) -> list[str]:
    role = design_role(path)
    if role == "model":
        return ["Ubiquitous Language", "Entities", "Value Objects", "State Transitions", "Domain ER Diagram", "Error Codes"]
    if role == "persistence":
        return ["PO Definitions", "Entity to PO Mapping", "Index Design", "Database ER Diagram", "DDL", "Capacity and Storage"]
    if role == "acl":
        return ["Business Module Scope", "Internal Dependencies", "External Dependencies and ACL", "Dependency Topology"]
    if role == "component":
        return ["Component Diagram", "Component Inventory", "Interface Contracts"]
    if role == "entrance":
        return ["Summary", "Access", "Request", "Response", "Error Codes", "Examples"]
    if role == "flow":
        return ["Approval Checklist", "Model Summary", "Entrance Summary", "Business Activity Diagram", "Sequence Diagram", "Exception Handling", "Robustness Constraints"]
    return []


def render_design_page(feature: FeatureSpec, context_dir: Path) -> str:
    lines = [
        f"# Feature {feature.feature_id} - Design View",
        "",
        "> L0 design view grouped by Shiki leaf specs. Each block cites the L1 file it came from.",
        "",
    ]
    if not feature.design_docs:
        lines.extend(["No feature design leaf specs were found.", ""])
        return "\n".join(lines)
    inventory_rows = [
        [design_role(path), title_from_markdown(path), source_code(path, context_dir)]
        for path in feature.design_docs
    ]
    lines.extend(["## Design Inventory", "", markdown_table(["role", "title", "source"], inventory_rows), ""])
    for path in feature.design_docs:
        text = read_text(path)
        lines.extend([f"## {title_from_markdown(path)}", "", source_note(path, context_dir), ""])
        selected = selected_sections_for(path)
        emitted = False
        for section in selected:
            body = extract_section(text, section)
            if not body:
                continue
            lines.extend([f"### {section}", "", body, ""])
            emitted = True
        if not emitted:
            lines.extend([short_body(text), ""])
    return "\n".join(lines)


def render_contract_page(feature: FeatureSpec, context_dir: Path) -> str:
    contract_path = feature.docs["code_contract"]
    test_path = feature.docs["test_cases"]
    contract = read_text(contract_path) if contract_path.exists() else ""
    sections = [
        "Metadata",
        "Entities",
        "DTOs",
        "Interfaces",
        "State Transitions",
        "Error Codes",
        "Non-functional Rules",
        "Change Log",
    ]
    lines = [
        f"# Feature {feature.feature_id} - Code Contract View",
        "",
        "> L0 view of the coding agreement. Coder agents still follow the L1 `code_contract.md` directly.",
        "",
        source_note(contract_path, context_dir) if contract_path.exists() else "> Source L1: missing `code_contract.md`",
        "",
    ]
    for section in sections:
        body = extract_section(contract, section)
        if body:
            lines.extend([f"## {section}", "", body, ""])
    lines.extend(["## Acceptance Coverage", ""])
    if test_path.exists():
        lines.extend([source_note(test_path, context_dir), "", short_body(read_text(test_path), max_lines=40), ""])
    else:
        lines.extend(["No `tests/test_cases.md` was found.", ""])
    return "\n".join(lines)


def render_module_page(module_dir: Path, context_dir: Path) -> str:
    index_path = module_dir / "index.md"
    index_text = read_text(index_path) if index_path.exists() else ""
    design_files = sorted((module_dir / "designs").glob("*.md")) if (module_dir / "designs").is_dir() else []
    entrance_files = sorted((module_dir / "entrances").glob("*.md")) if (module_dir / "entrances").is_dir() else []
    flow_files = sorted((module_dir / "flows").glob("*.md")) if (module_dir / "flows").is_dir() else []
    artifact_rows = []
    for role, paths in [("design", design_files), ("entrance", entrance_files), ("flow", flow_files)]:
        for path in paths:
            artifact_rows.append([role, title_from_markdown(path), source_code(path, context_dir)])
    lines = [
        f"# Module {module_dir.name} - Stable Spec View",
        "",
        "> L0 view of baseline module specs under `shiki_context/modules/`.",
        "",
    ]
    if index_path.exists():
        lines.extend(["## Boundary", "", source_note(index_path, context_dir), "", section_or_na(index_text, "Business Boundary"), ""])
        for section in ["Design Files", "Entrance Spec Files", "Flow Files", "Design Artifacts", "Entrance Spec Artifacts", "Flow Artifacts", "Loading Protocol"]:
            body = extract_section(index_text, section)
            if body:
                lines.extend([f"## {section}", "", body, ""])
    lines.extend(["## File Inventory", "", markdown_table(["role", "title", "source"], artifact_rows or [["N/A", "N/A", "N/A"]]), ""])
    return "\n".join(lines)


def render_gaps_page(model: ContextModel) -> str:
    missing_rows = []
    for feature in model.feature_specs:
        for target in feature.missing_targets:
            missing_rows.append([feature.feature_id, target])
        for role, path in feature.docs.items():
            if not path.exists():
                missing_rows.append([feature.feature_id, f"{role}: {relative_to(path, feature.path)}"])
    placeholder_rows = [
        [source_code(path, model.context_dir), line_no, line[:180]]
        for path, line_no, line in model.placeholders[:300]
    ]
    lines = [
        "# Gaps And Open Questions",
        "",
        "> L0 review aid. Resolve gaps in L1 specs, then regenerate this site.",
        "",
        "## Missing L1 Targets",
        "",
        markdown_table(["feature", "target"], missing_rows or [["None", "None"]]),
        "",
        "## Open Placeholders",
        "",
        markdown_table(["source", "line", "text"], placeholder_rows or [["None", "", ""]]),
        "",
    ]
    if len(model.placeholders) > 300:
        lines.extend([f"> Showing first 300 of {len(model.placeholders)} placeholder lines.", ""])
    return "\n".join(lines)


def write_generated_markdown(model: ContextModel, source_dir: Path, title: str) -> list[Path]:
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    pages: dict[Path, str] = {
        Path("README.md"): render_readme(model, title),
        Path("project.md"): render_project_page(model),
        Path("gaps.md"): render_gaps_page(model),
    }
    for feature in model.feature_specs:
        base = Path("features") / feature.feature_id
        pages[base / "overview.md"] = render_feature_overview(feature, model.context_dir)
        pages[base / "business.md"] = render_business_page(feature, model.context_dir)
        pages[base / "design.md"] = render_design_page(feature, model.context_dir)
        pages[base / "contract.md"] = render_contract_page(feature, model.context_dir)
    for module_dir in model.module_dirs:
        pages[Path("modules") / f"{module_dir.name}.md"] = render_module_page(module_dir, model.context_dir)
    written = []
    for relative, content in pages.items():
        path = source_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(path)
    return sorted(written)


def load_spec_to_html_module():
    script = Path(__file__).resolve().parents[2] / "spec-to-html" / "scripts" / "publish_docs.py"
    spec = importlib.util.spec_from_file_location("shiki_spec_to_html_publish_docs", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load spec-to-html publisher: {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.SITE_CSS = PRETTY_SITE_CSS
    return module


def install_pretty_table_renderer(publisher) -> None:
    original_render_table = publisher.render_table

    def render_pretty_table(lines, source, ctx):
        return '<div class="table-scroll">' + original_render_table(lines, source, ctx) + "</div>"

    publisher.render_table = render_pretty_table


def render_html_site(source_paths: list[Path], source_dir: Path, output_dir: Path, title: str, fail_on_broken_links: bool) -> int:
    publisher = load_spec_to_html_module()
    install_pretty_table_renderer(publisher)
    publisher.write_assets(
        publisher.RenderContext(
            title=title,
            base_dir=source_dir,
            output_dir=output_dir,
            generated_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            source_to_html={},
            source_root=source_dir,
        )
    )
    source_to_html = {
        source: publisher.target_path(source, source_dir, output_dir)
        for source in source_paths
    }
    ctx = publisher.RenderContext(
        title=title,
        base_dir=source_dir,
        output_dir=output_dir,
        generated_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        source_to_html=source_to_html,
        source_root=source_dir,
    )
    rendered_pages = []
    for source in source_paths:
        text = read_text(source)
        title_text = publisher.page_title(source, text)
        body = publisher.render_markdown(text, source, ctx)
        rendered_pages.append((source, source_to_html[source], title_text, body))
    page_index = [(source, html_path, title_text) for source, html_path, title_text, _ in rendered_pages]
    for source, html_path, title_text, body in rendered_pages:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        nav = publisher.render_nav(source, html_path, page_index, ctx)
        toc = publisher.render_toc(source, ctx)
        html_path.write_text(publisher.html_shell(title_text, source, body, nav, toc, ctx), encoding="utf-8")
    landing_name = "index.html"
    (output_dir / landing_name).write_text(publisher.render_landing(page_index, ctx, landing_name), encoding="utf-8")
    publisher.write_report(ctx, len(rendered_pages), landing_name)
    print(f"Published {len(rendered_pages)} L0 page(s) to {output_dir}")
    print(f"Landing page: {output_dir / landing_name}")
    if ctx.broken_links:
        print(f"Broken Markdown links: {len(ctx.broken_links)}")
        if fail_on_broken_links:
            return 2
    else:
        print("Broken Markdown links: 0")
    return 0


def publish_pretty(input_path: Path, output_dir: Path, title: str, feature: str | None, module: str | None, fail_on_broken_links: bool) -> int:
    model = build_context(input_path, feature, module)
    if not model.feature_specs and not model.module_dirs and model.project_dir is None:
        raise FileNotFoundError(
            "No Shiki specs found. Point the command at shiki_context/, a feature directory, or a module directory."
        )
    publisher = load_spec_to_html_module()
    publisher.prepare_output_dir(output_dir)
    source_dir = output_dir / GENERATED_SOURCE_DIR
    sources = write_generated_markdown(model, source_dir, title)
    return render_html_site(sources, source_dir, output_dir, title, fail_on_broken_links)


def parse_args(argv: list[str]) -> argparse.Namespace:
    project_root = find_project_root()
    parser = argparse.ArgumentParser(
        description="Publish Shiki L1 consensus specs as a human-friendly L0 HTML site."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="shiki_context/, a feature directory, a module directory, or a project root containing shiki_context/.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output root directory. The site is written to <output>/pretty_shiki_spec unless output is already named pretty_shiki_spec.",
    )
    parser.add_argument(
        "--title",
        default="Pretty Shiki Spec",
        help="HTML site title.",
    )
    parser.add_argument(
        "--feature",
        default=None,
        help="Publish only shiki_context/features/<feature>.",
    )
    parser.add_argument(
        "--module",
        default=None,
        help="Publish only shiki_context/modules/<module>.",
    )
    parser.add_argument(
        "--fail-on-broken-links",
        action="store_true",
        help="Exit non-zero if generated Markdown links point to missing pages.",
    )
    args = parser.parse_args(argv)
    args.project_root = project_root
    args.resolved_input = resolve_path(args.input, project_root)
    if args.output:
        output_root = Path(args.output).expanduser()
        output_root = output_root.resolve() if output_root.is_absolute() else (project_root / output_root).resolve()
    else:
        output_root = project_root
    args.resolved_output = pretty_spec_dir(output_root)
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return publish_pretty(
        input_path=args.resolved_input,
        output_dir=args.resolved_output,
        title=args.title,
        feature=args.feature,
        module=args.module,
        fail_on_broken_links=args.fail_on_broken_links,
    )


if __name__ == "__main__":
    raise SystemExit(main())
