#!/usr/bin/env python3
"""
Shiki Init scanner.

Default behavior runs the whole Init baseline pass:
1. discover Java entry points and write shiki_context/workspace/_plan.md
2. scan dependency and tech-stack context
3. execute every pending init.entrance workflow through devagent
4. execute init.sync once all entrances are analyzed

Compatibility flags keep the old S0.1/S0.2 split available for scripted checks.
"""

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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

ENTRANCE_CONTRACT = "core-kernel/runtime/task_contracts/init/entrance.yaml"
SYNC_CONTRACT = "core-kernel/runtime/task_contracts/init/sync.yaml"
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
        item_id = f"init.entrance.{index}"
        entrance_ids.append(item_id)
        rows.append(
            [
                f"`{item_id}`",
                "Init",
                f"`{entry.class_name}`",
                f"`{entry.module}`",
                "-",
                f"`{ENTRANCE_CONTRACT}`",
                "",
            ]
        )
    if entrance_ids:
        rows.append(
            [
                "`init.sync`",
                "Init",
                "`Discovery Log`",
                "-",
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


def run_devagent(prompt: str) -> int:
    try:
        return subprocess.run(["devagent", "--yolo", "-p", prompt], check=False).returncode
    except FileNotFoundError:
        print("[ERROR] devagent command not found; deep analysis cannot run.")
        print("        Entry discovery works offline; entry analysis requires a devagent-enabled environment.")
        return 127


def run_dependency_scan(config: ScanConfig) -> bool:
    prompt = f"""\
Run Scan Dependencies & Tech Stack.

# Reference Files
- {config.shiki_dir}/core-kernel/runtime/context_loading.md

# Scan Target
- Project root: {config.project_root}
- Source path: {config.src_root}
- Context output directory: {config.context_dir}

# Output Requirements
- Update {config.context_dir}/project/techstack.md with detected stack choices.
- Update {config.context_dir}/project/integration.md with data sources and external boundaries.
- Use only build files and configuration files; mark uncertain items as TBD.
"""
    targets = [
        config.context_path / "project" / "techstack.md",
        config.context_path / "project" / "integration.md",
    ]
    snap = snapshot_paths(targets)
    rc = run_devagent(prompt)
    ok = rc == 0 and paths_changed(snap)
    print(f"[DEPENDENCIES] {'OK' if ok else 'SKIP/FAIL'}")
    return ok


def snapshot_paths(paths: list[Path]) -> dict[Path, Optional[float]]:
    return {path: (path.stat().st_mtime if path.exists() else None) for path in paths}


def snapshot_tree(root: Path) -> dict[Path, Optional[float]]:
    if not root.exists():
        return {}
    return {path: path.stat().st_mtime for path in root.rglob("*.md") if path.is_file()}


def paths_changed(snap: dict[Path, Optional[float]]) -> bool:
    for path, old_mtime in snap.items():
        if not path.exists():
            continue
        if old_mtime is None or path.stat().st_mtime > old_mtime:
            return True
    return False


def relative_changed_paths(config: ScanConfig, snap: dict[Path, Optional[float]]) -> list[str]:
    changed = []
    for path, old_mtime in snap.items():
        if not path.exists():
            continue
        if old_mtime is None or path.stat().st_mtime > old_mtime:
            changed.append(str(path.relative_to(config.project_root)))
    return changed


def normalize_depends(depends_on: str) -> list[str]:
    clean = clean_cell(depends_on)
    if clean in EMPTY_VALUES:
        return []
    return [part.strip() for part in clean.split(",") if part.strip()]


def row_done(row: dict) -> bool:
    output = clean_cell(row.get("output_files", ""))
    return output not in EMPTY_VALUES and not output.upper().startswith("STALE")


def load_rows(config: ScanConfig) -> list[dict]:
    return existing_plan_items(config.plan_path)


def contract_matches(row: dict, contract_ref: str) -> bool:
    return clean_cell(row.get("contract", "")).endswith(contract_ref)


def next_ready_row(rows: list[dict], contract_ref: str) -> dict | None:
    completed = {clean_cell(row.get("id", "")) for row in rows if row_done(row)}
    for row in rows:
        if not contract_matches(row, contract_ref):
            continue
        if row_done(row):
            continue
        if any(dep not in completed for dep in normalize_depends(row.get("depends_on", ""))):
            continue
        return row
    return None


def class_to_src_path(config: ScanConfig, class_name: str) -> Path:
    prefix = config.base_package.rstrip(".") + "."
    if class_name.startswith(prefix):
        relative = class_name[len(prefix) :].replace(".", "/") + ".java"
        package_root = config.src_path / Path(config.base_package.replace(".", "/"))
        candidate = package_root / relative
        if candidate.exists():
            return candidate
    return config.src_path / Path(class_name.replace(".", "/")).with_suffix(".java")


def output_cell(paths: list[str]) -> str:
    if not paths:
        return ""
    return "<br>".join(f"`{path}`" for path in paths)


def update_plan_output(plan_path: Path, item_id: str, output_files: list[str]) -> None:
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or is_separator_row(stripped):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or clean_cell(cells[0]) != item_id:
            continue
        headers = find_table_headers(lines, index)
        try:
            output_index = headers.index("output_files")
        except ValueError:
            output_index = len(cells) - 1
        while len(cells) <= output_index:
            cells.append("")
        cells[output_index] = output_cell(output_files)
        lines[index] = "| " + " | ".join(cells) + " |"
        plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    raise ValueError(f"plan item not found: {item_id}")


def find_table_headers(lines: list[str], row_index: int) -> list[str]:
    for index in range(row_index - 1, -1, -1):
        stripped = lines[index].strip()
        if stripped.startswith("|") and not is_separator_row(stripped):
            return [clean_cell(cell) for cell in stripped.strip("|").split("|")]
    return []


def is_separator_row(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return bool(cells) and all(set(cell) <= {":", "-"} and "-" in cell for cell in cells)


def analyze_prompt(config: ScanConfig, row: dict) -> str:
    class_name = clean_cell(row["target"])
    module = clean_cell(row.get("module", "")) or infer_module(class_name, config.base_package)
    src_path = class_to_src_path(config, class_name)
    return f"""\
Run Entrance Analysis.

# Reference Files
- {config.shiki_dir}/core-kernel/runtime/context_loading.md
- {config.shiki_dir}/{ENTRANCE_CONTRACT}
- {config.shiki_dir}/core-kernel/workflows/init/entrance.md
- {config.context_dir}/project/architecture.md
- {config.context_dir}/project/ubiquitous_language.md
- {config.context_dir}/modules/{module}/index.md

# Current Task
- Fully qualified class: {class_name}
- Source file: {src_path}
- Module: {module}

# Deep Analysis Requirements
1. Read the entry source and trace Controller/Listener/Job -> Service -> Domain -> Repository/Support calls.
2. Generate or update `entrances/*.md` with Method, URL, request, and response contracts.
3. Generate or update `flows/*.md` with sequence, architecture audit, and Discovery Log.
4. Append updates to {config.context_dir}/modules/{module}/index.md and {config.context_dir}/project/ubiquitous_language.md.
5. Do not stop at an entry list; finish call-chain tracing before returning.
"""


def changed_markdown_files(before: dict[Path, Optional[float]], roots: list[Path]) -> list[Path]:
    candidates = set(before)
    for root in roots:
        if root.exists():
            candidates.update(path for path in root.rglob("*.md") if path.is_file())
    changed = []
    for path in sorted(candidates):
        old_mtime = before.get(path)
        if not path.exists():
            continue
        if old_mtime is None or path.stat().st_mtime > old_mtime:
            changed.append(path)
    return changed


def analyze_one(config: ScanConfig, row: dict) -> bool:
    item_id = clean_cell(row["id"])
    class_name = clean_cell(row["target"])
    module = clean_cell(row.get("module", "")) or infer_module(class_name, config.base_package)
    module_dir = config.context_path / "modules" / module
    ensure_module_workspace(config, module)
    roots = [module_dir / "entrances", module_dir / "flows"]
    before = {}
    before.update(snapshot_tree(module_dir / "entrances"))
    before.update(snapshot_tree(module_dir / "flows"))
    for path in [module_dir / "index.md", config.context_path / "project" / "ubiquitous_language.md"]:
        before[path] = path.stat().st_mtime if path.exists() else None

    print(f"[ANALYZE] {item_id}: {class_name} (module={module})")
    rc = run_devagent(analyze_prompt(config, row))
    changed = changed_markdown_files(before, roots)
    output_files = [
        str(path.relative_to(config.project_root))
        for path in changed
        if "entrances" in path.parts or "flows" in path.parts
    ]
    if rc == 0 and output_files:
        update_plan_output(config.plan_path, item_id, output_files)
        print(f"[ANALYZE] OK: {', '.join(output_files)}")
        return True

    print(f"[ANALYZE] FAIL: rc={rc}, no entrances/flows output detected")
    return False


def sync_prompt(config: ScanConfig) -> str:
    return f"""\
Run Discovery Sync.

# Reference Files
- {config.shiki_dir}/core-kernel/runtime/context_loading.md
- {config.shiki_dir}/{SYNC_CONTRACT}
- {config.shiki_dir}/core-kernel/workflows/init/sync.md

# Current Task
- Build the completed flow list from {config.context_dir}/workspace/_plan.md and module indexes.
- Read Discovery Log or architecture audit snippets by module or flow batch; do not load every flow body at once.
- Aggregate cross-module dependencies, MQ topics, external systems, and architecture violations.

# Output Requirements
- Update {config.context_dir}/project/architecture.md.
- Update {config.context_dir}/project/integration.md.
- Create or update {config.context_dir}/project/tech_debt.md.
"""


def run_sync(config: ScanConfig, row: dict) -> bool:
    item_id = clean_cell(row["id"])
    targets = [
        config.context_path / "project" / "architecture.md",
        config.context_path / "project" / "integration.md",
        config.context_path / "project" / "tech_debt.md",
    ]
    snap = snapshot_paths(targets)
    print("[SYNC] aggregating Discovery Logs")
    rc = run_devagent(sync_prompt(config))
    changed = relative_changed_paths(config, snap)
    if rc == 0 and changed:
        update_plan_output(config.plan_path, item_id, changed)
        print(f"[SYNC] OK: {', '.join(changed)}")
        return True
    print(f"[SYNC] FAIL/SKIP: rc={rc}, no sync output detected")
    return False


def run_analysis(config: ScanConfig, skip_on_error: bool = False, max_items: Optional[int] = None) -> bool:
    if not config.plan_path.exists() or not load_rows(config):
        discover(config)

    completed = 0
    failed = 0
    while True:
        if max_items is not None and completed >= max_items:
            print(f"[STOP] reached max-items={max_items}")
            return failed == 0
        rows = load_rows(config)
        row = next_ready_row(rows, "init/entrance.yaml")
        if row is None:
            break
        if analyze_one(config, row):
            completed += 1
            continue
        failed += 1
        if not skip_on_error:
            return False
    print(f"[ANALYZE] entry analysis complete: success={completed}, failed={failed}")

    rows = load_rows(config)
    sync_row = next_ready_row(rows, "init/sync.yaml")
    if sync_row is not None:
        return run_sync(config, sync_row) and failed == 0
    return failed == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shiki Init scanner and baseline analyzer.")
    parser.add_argument("--only", choices=["s0.1", "s0.2"], help="legacy S0 compatibility: s0.1=discover, s0.2=dependency scan")
    parser.add_argument("--discover-only", action="store_true", help="only discover entries and write _plan.md")
    parser.add_argument("--analyze-only", action="store_true", help="only run pending entry analysis and sync; discover first when plan is empty")
    parser.add_argument("--sync-only", action="store_true", help="only run init.sync")
    parser.add_argument("--force-discover", action="store_true", help="rebuild the Init _plan.md")
    parser.add_argument("--skip-on-error", action="store_true", help="continue after an entry analysis failure")
    parser.add_argument("--max-items", type=int, default=None, help="maximum number of entries to analyze")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    ensure_context_dirs(config)

    if args.only == "s0.1" or args.discover_only:
        discover(config, force=args.force_discover)
        return 0
    if args.only == "s0.2":
        return 0 if run_dependency_scan(config) else 1
    if args.sync_only:
        rows = load_rows(config)
        sync_row = next_ready_row(rows, "init/sync.yaml")
        if sync_row is None:
            print("[SYNC] no runnable init.sync task.")
            return 0
        return 0 if run_sync(config, sync_row) else 1

    if not config.plan_path.exists() or not load_rows(config) or args.force_discover:
        discover(config, force=args.force_discover)
    run_dependency_scan(config)
    return 0 if run_analysis(config, skip_on_error=args.skip_on_error, max_items=args.max_items) else 1


if __name__ == "__main__":
    raise SystemExit(main())
