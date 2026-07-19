#!/usr/bin/env python3
"""
Shiki Init scanner.

This low-level helper performs lightweight entry discovery and writes the
Canonical Init Plan. The CLI automatic track or Prompt manual track then
executes one Plan Task at a time through the shared Kernel Task Tools.
"""

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SHIKI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SHIKI_ROOT / "core-kernel"))

from _lib.markdown import extract_section, parse_table, read_text


DDD_LAYER_SEGMENTS = {"adapter", "application", "domain", "infrastructure"}
ENTRY_SUFFIXES = (
    "Controller.java",
    "Endpoint.java",
    "Resource.java",
    "Listener.java",
    "Consumer.java",
    "Job.java",
    "Task.java",
    "Scheduler.java",
)
ENTRY_MARKERS = (
    "@RestController",
    "@Controller",
    "@RequestMapping",
    "@GetMapping",
    "@PostMapping",
    "@PutMapping",
    "@PatchMapping",
    "@DeleteMapping",
    "@KafkaListener",
    "@RabbitListener",
    "@JmsListener",
    "@Scheduled",
    "@MessageMapping",
)

ENTRANCE_CONTRACT = "init/inspect_controller.yaml"
SYNC_CONTRACT = "init/sync_plan.yaml"
EMPTY_VALUES = {"", "-", "`-`"}


@dataclass(frozen=True)
class ScanConfig:
    project_root: Path
    shiki_root: Path
    src_root: str
    base_package: str
    shiki_dir: str
    context_dir: str

    @property
    def src_path(self) -> Path:
        return self.project_root / self.src_root

    @property
    def context_path(self) -> Path:
        return self.project_root / self.context_dir

    @property
    def plan_path(self) -> Path:
        return self.context_path / "workspace" / "_plan.md"


@dataclass(frozen=True)
class EntryPoint:
    class_name: str
    source_path: Path
    module: str


def _strip_comment(value: str) -> str:
    if "#" not in value:
        return value.strip()
    return value.split("#", 1)[0].strip()


def _parse_yaml(path: Path) -> dict:
    result = {}
    current_key = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- ") and current_key:
            result.setdefault(current_key, []).append(_strip_comment(stripped[2:]).strip("\"'"))
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        current_key = key.strip()
        value = _strip_comment(value).strip("\"'")
        result[current_key] = value if value else []
    return result


def load_config() -> ScanConfig:
    shiki_root = SHIKI_ROOT
    inferred_root = shiki_root.parent
    candidates = [inferred_root, Path.cwd(), *Path.cwd().parents]
    seen = set()
    config = {}
    project_root = inferred_root
    for directory in candidates:
        if directory in seen:
            continue
        seen.add(directory)
        cfg_path = directory / "shiki.config.yaml"
        if cfg_path.exists():
            config = _parse_yaml(cfg_path)
            project_root = directory
            print(f"[CONFIG] loaded config: {cfg_path}")
            break
    else:
        print("[WARN] shiki.config.yaml not found; using defaults.")

    return ScanConfig(
        project_root=project_root,
        shiki_root=shiki_root,
        src_root=config.get("src_root", "src/main/java"),
        base_package=config.get("base_package", "com.example"),
        shiki_dir=config.get("shiki_dir", "shiki"),
        context_dir=config.get("context_dir", "shiki_context"),
    )


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "|" + "|".join(":---" for _ in headers) + "|"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator] + body)


def ensure_context_dirs(config: ScanConfig) -> None:
    (config.context_path / "workspace").mkdir(parents=True, exist_ok=True)
    (config.context_path / "project").mkdir(parents=True, exist_ok=True)
    (config.context_path / "modules").mkdir(parents=True, exist_ok=True)
    (config.context_path / "features").mkdir(parents=True, exist_ok=True)


def is_entry_source(path: Path, text: str) -> bool:
    if any(path.name.endswith(suffix) for suffix in ENTRY_SUFFIXES):
        return True
    return any(marker in text for marker in ENTRY_MARKERS)


def java_class_name(path: Path, src_path: Path, text: str) -> str:
    package_match = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.M)
    if package_match:
        return f"{package_match.group(1)}.{path.stem}"
    relative = path.relative_to(src_path).with_suffix("")
    return ".".join(relative.parts)


def infer_module(class_name: str, base_package: str) -> str:
    prefix = base_package.rstrip(".") + "."
    if class_name.startswith(prefix):
        parts = class_name[len(prefix) :].split(".")
        if len(parts) >= 2 and parts[0] in DDD_LAYER_SEGMENTS:
            return parts[1]
        return parts[0] if parts else "default"
    parts = class_name.split(".")
    return parts[-3] if len(parts) >= 3 else (parts[0] if parts else "default")


def discover_entries(config: ScanConfig) -> list[EntryPoint]:
    if not config.src_path.exists():
        raise FileNotFoundError(f"src_root does not exist: {config.src_path}")

    entries = []
    for path in sorted(config.src_path.rglob("*.java")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        if not is_entry_source(path, text):
            continue
        class_name = java_class_name(path, config.src_path, text)
        entries.append(
            EntryPoint(
                class_name=class_name,
                source_path=path,
                module=infer_module(class_name, config.base_package),
            )
        )
    return entries


def copy_template_file(src: Path, dst: Path, module: str) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".md":
        content = src.read_text(encoding="utf-8").replace("[ModuleName]", module)
        dst.write_text(content, encoding="utf-8")
    else:
        shutil.copy2(src, dst)


def ensure_module_workspace(config: ScanConfig, module: str) -> None:
    template_dir = config.shiki_root / "core-kernel" / "templates" / "module"
    module_dir = config.context_path / "modules" / module
    module_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ["entrances", "flows", "designs"]:
        (module_dir / subdir).mkdir(parents=True, exist_ok=True)
    if not template_dir.exists():
        return
    for src in sorted(template_dir.rglob("*")):
        if not src.is_file():
            continue
        relative = src.relative_to(template_dir)
        if relative.name.startswith("_") and relative.as_posix() != "_plan.md":
            continue
        copy_template_file(src, module_dir / relative, module)


def existing_plan_items(plan_path: Path) -> list[dict]:
    if not plan_path.exists():
        return []
    text = read_text(plan_path)
    legacy_heading = "Target " + "Arti" + "facts"
    section = extract_section(text, "Target Outputs") or extract_section(text, legacy_heading)
    return parse_table(section)


def write_plan(config: ScanConfig, entries: list[EntryPoint], force: bool = False) -> bool:
    existing = existing_plan_items(config.plan_path)
    if existing and not force:
        print(f"[DISCOVER] existing plan found; skipping rebuild: {config.plan_path}")
        return False

    rows = []
    entrance_ids = []
    for index, entry in enumerate(entries, start=1):
        item_id = f"inspect-{index:03d}"
        entrance_ids.append(item_id)
        rows.append(
            [
                f"`{item_id}`",
                "Init",
                f"`{entry.source_path.relative_to(config.project_root)}`",
                f"`{entry.module}`",
                "",
                f"`{ENTRANCE_CONTRACT}`",
                "",
            ]
        )
    if entrance_ids:
        rows.append(
            [
                "`sync-plan`",
                "Init",
                "`workspace/_plan.md`",
                "`workspace`",
                ",".join(entrance_ids),
                f"`{SYNC_CONTRACT}`",
                "",
            ]
        )

    table = markdown_table(
        ["id", "phase", "target", "module", "depends_on", "contract", "output_files"],
        rows,
    )
    config.plan_path.parent.mkdir(parents=True, exist_ok=True)
    config.plan_path.write_text(
        "\n".join(
            [
                "# Scan Plan",
                "",
                "> Local Init/scan queue: task routing plus output tracking.",
                "> After `scan.py` registers entry tasks, it can run entry analysis and global sync.",
                "> This file is not long-lived phase progress; feature progress lives in `features/{feature}/_plan.md`.",
                "",
                "## Target Outputs",
                "",
                table,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"[DISCOVER] found {len(entries)} entries; wrote {config.plan_path}")
    return True


def ensure_architecture_baseline(config: ScanConfig, entries: list[EntryPoint]) -> None:
    arch_path = config.context_path / "project" / "architecture.md"
    if not arch_path.exists():
        arch_path.write_text("# System Architecture\n\n## 2. Module Overview\n\n", encoding="utf-8")
    content = arch_path.read_text(encoding="utf-8")
    lines = []
    modules = sorted({entry.module for entry in entries})
    for module in modules:
        if f"`modules/{module}/index.md`" in content or f"| {module} |" in content:
            continue
        lines.append(f"| {module} | Pending analysis | `modules/{module}/index.md` | pending |")
    if not lines:
        return
    if "| module | responsibility | spec path | status |" not in content:
        addition = [
            "",
            "### Module Inventory",
            "",
            "| module | responsibility | spec path | status |",
            "| :--- | :--- | :--- | :--- |",
            *lines,
            "",
        ]
    else:
        addition = ["", *lines]
    arch_path.write_text(content.rstrip() + "\n" + "\n".join(addition), encoding="utf-8")


def insert_rows_in_section_table(content: str, heading: str, rows: list[str]) -> str:
    """Insert rows into a markdown table under a heading."""
    lines = [
        line
        for line in content.splitlines()
        if "*(scan or design task appends here)*" not in line
    ]
    try:
        heading_index = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return content.rstrip() + "\n\n" + heading + "\n\n" + "\n".join(
            [
                "| module | path | index | status |",
                "| :--- | :--- | :--- | :--- |",
                *rows,
            ]
        ) + "\n"

    insert_at = None
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## ") and index > heading_index + 1:
            insert_at = index
            break
        if stripped.startswith("|"):
            insert_at = index + 1
            while insert_at < len(lines) and lines[insert_at].strip().startswith("|"):
                insert_at += 1
            break
    if insert_at is None:
        insert_at = len(lines)

    for row in reversed(rows):
        lines.insert(insert_at, row)
    return "\n".join(lines).rstrip() + "\n"


def ensure_project_index(config: ScanConfig, entries: list[EntryPoint]) -> None:
    index_path = config.context_path / "project" / "index.md"
    if not index_path.exists():
        template_path = config.shiki_root / "core-kernel" / "templates" / "project" / "index.md"
        if template_path.exists():
            copy_template_file(template_path, index_path, "project")
        else:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text("# Project Spec Index\n\n", encoding="utf-8")

    content = index_path.read_text(encoding="utf-8")
    rows = []
    for module in sorted({entry.module for entry in entries}):
        if f"| `{module}` |" in content or f"| {module} |" in content:
            continue
        rows.append(f"| `{module}` | `modules/{module}/` | `modules/{module}/index.md` | current |")
    if rows:
        index_path.write_text(insert_rows_in_section_table(content, "## Module Registry", rows), encoding="utf-8")


def discover(config: ScanConfig, force: bool = False) -> list[EntryPoint]:
    ensure_context_dirs(config)
    entries = discover_entries(config)
    for entry in entries:
        ensure_module_workspace(config, entry.module)
    ensure_architecture_baseline(config, entries)
    ensure_project_index(config, entries)
    write_plan(config, entries, force=force)
    return entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover entries and create the Shiki V4 Init Plan.")
    parser.add_argument("--discover-only", action="store_true", help="Compatibility flag; discovery is the only action.")
    parser.add_argument("--force-discover", action="store_true", help="Rebuild the Init Plan.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    ensure_context_dirs(config)
    discover(config, force=args.force_discover)
    print("[NEXT] run `shiki scan` or `/shiki-scan` to execute one Init Task per Agent session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
