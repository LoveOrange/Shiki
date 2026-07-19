"""Console entrypoint for installing and dispatching Shiki helpers."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__


DEFAULT_SOURCE = "https://github.com/LoveOrange/Shiki.git"
DEFAULT_SHIKI_DIR = "shiki"
SUPPORTED_TOOLS = ("codex", "claude", "gemini", "opencode", "all")
COPY_DIRS = ("docs", "core-kernel", "tools-skills", "tech-stacks", "providers", "user-interface")
COPY_FILES = ("AGENTS.md", "LICENSE", "README.md", "shiki.config.yaml")


class CliError(RuntimeError):
    """Raised for user-facing command errors."""


PROVIDER_STATUS_RE = re.compile(
    r"^(PASS|BLOCKED|FAILED|MANUAL_DECISION|CHANGE_REQUEST)(?::\s*(.*))?$"
)


def run(cmd: list[str], cwd: Path) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def ensure_project_root(path: str) -> Path:
    project_root = Path(path).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise CliError(f"project root does not exist: {project_root}")
    return project_root


def is_git_worktree(project_root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(project_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def is_local_source(source: str) -> bool:
    return Path(source).expanduser().exists()


def resolve_shiki_root(project_root: Path, shiki_dir: str) -> Path:
    shiki_root = (project_root / shiki_dir).resolve()
    if shiki_root.exists():
        return shiki_root
    raise CliError(f"Shiki framework directory not found: {shiki_root}. Run `shiki install` first.")


def require_script(shiki_root: Path, relative: str) -> Path:
    script = shiki_root / relative
    if not script.exists():
        raise CliError(f"Shiki script not found: {script}")
    return script


def run_shiki_script(project_root: Path, shiki_dir: str, relative: str, args: list[str]) -> None:
    shiki_root = resolve_shiki_root(project_root, shiki_dir)
    script = require_script(shiki_root, relative)
    run([sys.executable, str(script), *args], cwd=project_root)


def copy_framework(source: str, destination: Path) -> None:
    source_root = Path(source).expanduser().resolve()
    if not source_root.exists() or not source_root.is_dir():
        raise CliError(f"local Shiki source does not exist: {source_root}")
    if destination.exists():
        raise CliError(f"target Shiki directory already exists: {destination}")
    for name in COPY_DIRS:
        if not (source_root / name).exists():
            raise CliError(f"local Shiki source is missing required directory: {name}")

    destination.mkdir(parents=True)
    for name in COPY_DIRS:
        shutil.copytree(source_root / name, destination / name)
    for name in COPY_FILES:
        src = source_root / name
        if src.exists():
            shutil.copy2(src, destination / name)


def select_install_mode(project_root: Path, source: str, requested: str) -> str:
    if requested != "auto":
        return requested
    if is_local_source(source):
        return "copy"
    if is_git_worktree(project_root):
        return "submodule"
    return "clone"


def install_framework(args: argparse.Namespace) -> None:
    project_root = ensure_project_root(args.project_root)
    destination = (project_root / args.shiki_dir).resolve()

    if destination.exists():
        print(f"Shiki root ready: {destination} (existing)", flush=True)
        return

    mode = select_install_mode(project_root, args.source, args.mode)
    if mode == "copy":
        if not is_local_source(args.source):
            raise CliError("--mode copy requires a local --source path")
        copy_framework(args.source, destination)
    elif mode == "submodule":
        command = ["git", "submodule", "add"]
        if args.ref:
            command.extend(["-b", args.ref])
        command.extend([args.source, args.shiki_dir])
        run(command, cwd=project_root)
    elif mode == "clone":
        command = ["git", "clone"]
        if args.ref:
            command.extend(["--branch", args.ref])
        command.extend([args.source, args.shiki_dir])
        run(command, cwd=project_root)
    else:
        raise CliError(f"unsupported install mode: {mode}")

    print(f"Shiki root ready: {destination} ({mode})", flush=True)


def command_install(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    install_framework(args)
    if not args.skip_init:
        init_args = []
        if args.force_context:
            init_args.append("--force")
        run_shiki_script(project_root, args.shiki_dir, "tools-skills/scripts/init.py", init_args)
    if not args.skip_adapter:
        run_shiki_script(
            project_root,
            args.shiki_dir,
            "tools-skills/scripts/install_agent_adapter.py",
            ["--tool", args.tool],
        )
    return 0


def command_init(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    script_args = []
    if args.target:
        script_args.extend(["--target", args.target])
    if args.force:
        script_args.append("--force")
    run_shiki_script(project_root, args.shiki_dir, "tools-skills/scripts/init.py", script_args)
    return 0


def command_new_feature(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    run_shiki_script(
        project_root,
        args.shiki_dir,
        "tools-skills/scripts/new_feature.py",
        ["--taskid", args.taskid],
    )
    return 0


def command_adapter_install(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    script_args = ["--tool", args.tool]
    if args.dry_run:
        script_args.append("--dry-run")
    run_shiki_script(
        project_root,
        args.shiki_dir,
        "tools-skills/scripts/install_agent_adapter.py",
        script_args,
    )
    return 0


def load_runtime(shiki_root: Path) -> None:
    """Make the project-local Core Kernel importable without installing it."""
    kernel_path = str(shiki_root / "core-kernel")
    if kernel_path not in sys.path:
        sys.path.insert(0, kernel_path)
    source_path = str(shiki_root)
    if source_path not in sys.path:
        sys.path.insert(0, source_path)


def clean_plan_cell(value: str) -> str:
    return str(value or "").strip().strip("`").strip()


def active_task_field(project_root: Path, field: str) -> str:
    path = project_root / "shiki_context" / "workspace" / "active_task.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"^\s*-\s+`{re.escape(field)}`:\s*`?([^`\n]+)`?",
        rf"^\s*-\s+\*\*.*{re.escape(field)}.*\*\*:\s*`?([^`\n]+)`?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.M | re.I)
        if not match:
            continue
        value = clean_plan_cell(match.group(1))
        if value.startswith("[") and value.endswith("]"):
            return ""
        if value.lower() in {"", "-", "auto", "n/a", "none", "null"}:
            return "" if field != "next" else "auto"
        return value
    return ""


def runtime_scope(project_root: Path, expected_kind: str = "") -> tuple[Path, str]:
    context = project_root / "shiki_context"
    if not context.is_dir():
        raise CliError(f"shiki_context not found: {context}. Run `shiki init` first.")
    if expected_kind == "sync":
        return context / "workspace", "sync"
    stage = active_task_field(project_root, "stage").lower()
    if stage == "init":
        if expected_kind and expected_kind != "init":
            raise CliError("next requires an active feature stage")
        return context / "workspace", "init"
    if expected_kind == "init":
        raise CliError("scan requires active_task.stage = Init")
    feature = active_task_field(project_root, "feature")
    if not feature:
        raise CliError("active_task.feature is required")
    target = context / "features" / feature
    if not target.is_dir():
        raise CliError(f"active feature not found: {target}")
    return target, "feature"


def prepare_kernel_task(
    project_root: Path,
    shiki_root: Path,
    requested_item: str = "",
    expected_kind: str = "",
    apply_policy: bool = True,
    refresh_plan: bool = False,
):
    load_runtime(shiki_root)
    from _lib.task_tools import next_task, skip_optional_init_flows

    scope_dir, scope_kind = runtime_scope(project_root, expected_kind)
    skipped = ()
    if scope_kind == "init" and apply_policy:
        skipped, blocker = skip_optional_init_flows(project_root, scope_dir)
        if blocker:
            raise CliError(blocker)
    prepared = next_task(
        shiki_root=shiki_root,
        project_root=project_root,
        feature_dir=scope_dir,
        requested_item=clean_plan_cell(requested_item),
        scope_kind=scope_kind,
        plan_path=(scope_dir / "sync_plan.md") if scope_kind == "sync" else None,
        refresh_plan=refresh_plan,
    )
    return scope_dir, scope_kind, prepared, skipped


def command_task_next(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    _, _, prepared, skipped = prepare_kernel_task(
        project_root,
        shiki_root,
        requested_item=args.item or "",
        expected_kind="" if args.scope == "auto" else args.scope,
    )
    if skipped:
        print("Skipped optional Init Flow items: " + ", ".join(skipped), file=sys.stderr)
    print(
        prepared.render_markdown(),
        end="",
        file=sys.stdout if prepared.status in {"READY", "DONE"} else sys.stderr,
    )
    return 0 if prepared.status in {"READY", "DONE"} else 1


def command_task_complete(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    load_runtime(shiki_root)
    from _lib.task_tools import complete_task

    requested_scope = "" if args.scope == "auto" else args.scope
    scope_dir, scope_kind = runtime_scope(project_root, requested_scope)
    completion = complete_task(
        project_root=project_root,
        feature_dir=scope_dir,
        task_id=clean_plan_cell(args.task_id),
        output_files=tuple(args.output or ()),
        noop_reason=args.noop or "",
        scope_kind=scope_kind,
        plan_path=(scope_dir / "sync_plan.md") if scope_kind == "sync" else None,
    )
    print(
        completion.render_markdown(),
        end="",
        file=sys.stdout if completion.status == "PASS" else sys.stderr,
    )
    return 0 if completion.status == "PASS" else 1


def command_plan_add_item(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    load_runtime(shiki_root)
    from _lib.task_tools import plan_add_items

    scope_dir, _ = runtime_scope(project_root)
    result = plan_add_items(
        feature_dir=scope_dir,
        parent_task_id=clean_plan_cell(args.parent),
        new_items=[
            {
                "id": args.id,
                "phase": args.phase,
                "target": args.target,
                "module": args.module or "",
                "depends_on": args.depends_on or "",
                "contract": args.contract,
                "output_files": "",
            }
        ],
    )
    print(result.render_markdown(), end="", file=sys.stdout if result.status == "PASS" else sys.stderr)
    return 0 if result.status == "PASS" else 1


def provider_status(output: str) -> str:
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line:
            match = PROVIDER_STATUS_RE.fullmatch(line)
            return match.group(1) if match else ""
    return ""


def provider_settings(project_root: Path, shiki_root: Path, override: str):
    load_runtime(shiki_root)
    from _lib.config import load_project_config

    provider = load_project_config(project_root).get("provider", {})
    if isinstance(provider, str):
        provider = {"name": provider}
    if not isinstance(provider, dict):
        provider = {}
    name = (
        override
        or os.environ.get("SHIKI_PROVIDER", "").strip()
        or str(provider.get("name", "")).strip()
        or "codex"
    ).lower()
    model = os.environ.get("SHIKI_PROVIDER_MODEL", "").strip() or str(provider.get("model", "")).strip()
    executable = (
        os.environ.get(f"SHIKI_{name.upper()}_EXECUTABLE", "").strip()
        or str(provider.get("executable", "")).strip()
        or name
    )
    return name, executable, model


def configured_provider(project_root: Path, shiki_root: Path, override: str):
    load_runtime(shiki_root)
    from providers import create_provider

    name, executable, model = provider_settings(project_root, shiki_root, override)
    try:
        return create_provider(name, project_root, executable=executable, model=model)
    except ValueError as exc:
        raise CliError(str(exc)) from exc


def phase_complete(shiki_root: Path, scope_dir: Path, phase: str, scope_kind: str = "feature") -> bool:
    load_runtime(shiki_root)
    from _lib.feature_plan import parse_plan
    from _lib.kernel import item_done

    plan_path = scope_dir / "sync_plan.md" if scope_kind == "sync" else scope_dir / "_plan.md"
    _, items = parse_plan(plan_path)
    phase_items = [item for item in items if clean_plan_cell(item.get("phase", "")) == phase]
    return bool(phase_items) and all(item_done(scope_dir, item) for item in phase_items)


def run_provider(provider, prompt: str, read_only: bool = False):
    result = provider.execute_prompt(prompt, read_only=read_only)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise CliError(f"provider exited with {result.returncode}")
    status = provider_status(result.stdout)
    if not status:
        raise CliError("provider response must start with '<STATUS>: <summary>'")
    return status


def execute_automatic(args: argparse.Namespace, expected_kind: str, prompt_command: str = "next") -> int:
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    load_runtime(shiki_root)
    from _lib.config import orchestration_granularity
    from _lib.prompt_builder import build_execution_prompt
    from _lib.task_tools import complete_task
    provider = configured_provider(project_root, shiki_root, args.provider)
    granularity = orchestration_granularity(project_root)
    max_steps = min(args.max_steps, args.steps) if args.steps else args.max_steps

    for _ in range(max_steps):
        scope_dir, scope_kind, prepared, skipped = prepare_kernel_task(
            project_root,
            shiki_root,
            requested_item=args.item if expected_kind == "feature" else "",
            expected_kind=expected_kind,
            refresh_plan=expected_kind == "sync" and bool(args.tail),
        )
        if skipped:
            print("Skipped optional Init Flow items: " + ", ".join(skipped), file=sys.stderr)
        if prepared.status == "DONE":
            print("DONE: plan complete")
            return 0
        if prepared.status != "READY":
            raise CliError(prepared.blocker or "no ready task")

        task_id = prepared.task_id
        phase = clean_plan_cell(prepared.route.item.get("phase", ""))
        status = run_provider(
            provider,
            build_execution_prompt(prompt_command, args.tail or "", envelope=prepared.envelope),
        )
        if status != "PASS":
            raise CliError(f"provider returned {status}")

        completion = complete_task(
            project_root=project_root,
            feature_dir=scope_dir,
            task_id=task_id,
            scope_kind=scope_kind,
            plan_path=prepared.plan_path,
        )
        if completion.status != "PASS":
            raise CliError(completion.message or f"ledger did not advance for item {task_id}")

        _, _, after, _ = prepare_kernel_task(
            project_root,
            shiki_root,
            expected_kind=expected_kind,
            apply_policy=False,
        )
        if after.status == "READY" and after.task_id == task_id:
            raise CliError(f"ledger did not advance for item {task_id}")
        if after.status == "BLOCKED":
            raise CliError(after.blocker)

        at_phase_boundary = phase_complete(shiki_root, scope_dir, phase, scope_kind)
        if granularity == "task" or at_phase_boundary:
            review_status = run_provider(
                provider,
                build_execution_prompt(
                    "review",
                    f"Review {scope_kind} task {task_id} at the {phase} boundary.",
                ),
                read_only=True,
            )
            if review_status == "CHANGE_REQUEST":
                raise CliError("Review returned CHANGE_REQUEST; apply changes explicitly, then continue")
            if review_status != "PASS":
                raise CliError(f"Review returned {review_status}")

        if granularity == "task" or (granularity == "phase" and at_phase_boundary):
            return 0
        if after.status == "DONE":
            print("DONE: plan complete")
            return 0
        args.item = ""
        args.tail = ""

    raise CliError(f"reached --max-steps {max_steps} before the {granularity} boundary")


def command_next(args: argparse.Namespace) -> int:
    return execute_automatic(args, "feature")


def command_scan(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    plan_path = project_root / "shiki_context" / "workspace" / "_plan.md"
    if not plan_path.is_file() or not plan_path.read_text(encoding="utf-8").strip():
        run_shiki_script(project_root, args.shiki_dir, "tools-skills/scripts/scan.py", [])
    return execute_automatic(args, "init")


def command_sync(args: argparse.Namespace) -> int:
    return execute_automatic(args, "sync", prompt_command="sync")


def command_provider_prompt(args: argparse.Namespace) -> int:
    """Run one non-plan command in a fresh configured Provider process."""
    project_root = ensure_project_root(args.project_root)
    shiki_root = resolve_shiki_root(project_root, args.shiki_dir)
    load_runtime(shiki_root)
    from _lib.prompt_builder import build_execution_prompt
    provider = configured_provider(project_root, shiki_root, args.provider)
    status = run_provider(
        provider,
        build_execution_prompt(args.command, args.tail or ""),
        read_only=args.command in {"status", "review", "doctor"},
    )
    if status in {"BLOCKED", "FAILED", "MANUAL_DECISION"}:
        raise CliError(f"provider returned {status}")
    if status == "CHANGE_REQUEST" and args.command != "review":
        raise CliError(f"{args.command} cannot return CHANGE_REQUEST")
    return 0


def resolve_codebomb_script(project_root: Path, shiki_dir: str) -> Path:
    project_local_script = project_root / shiki_dir / "tools-skills" / "scripts" / "codebomb.py"
    if project_local_script.exists():
        return project_local_script.resolve()
    source_script = Path(__file__).resolve().parents[1] / "tools-skills" / "scripts" / "codebomb.py"
    if source_script.exists():
        return source_script.resolve()
    raise CliError("Codebomb script not found. Expected tools-skills/scripts/codebomb.py.")


def resolve_codebomb_python(project_root: Path) -> str:
    for relative in [
        ".shiki/tools/codebomb/venv/bin/python",
        ".shiki/tools/codebomb/venv/Scripts/python.exe",
    ]:
        candidate = project_root / relative
        if candidate.exists():
            return str(candidate.resolve())
    return sys.executable


def command_tool_codebomb(args: argparse.Namespace) -> int:
    project_root = ensure_project_root(args.project_root)
    repo = Path(args.repo).expanduser()
    if not repo.is_absolute():
        repo = project_root / repo
    repo = repo.resolve()
    if not repo.is_dir():
        raise CliError(f"repo does not exist: {repo}")
    script = resolve_codebomb_script(project_root, args.shiki_dir)
    python = resolve_codebomb_python(project_root)
    result = subprocess.run([python, str(script), "--repo", str(repo)], cwd=str(project_root))
    return result.returncode


def add_common_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Consumer project root. Defaults to the current directory.")
    parser.add_argument("--shiki-dir", default=DEFAULT_SHIKI_DIR, help="Project-local Shiki directory. Defaults to shiki/.")


def add_automatic_args(parser: argparse.ArgumentParser) -> None:
    add_common_project_args(parser)
    parser.add_argument(
        "--provider",
        choices=("codex", "claude"),
        default="",
        help="CLI Provider. Overrides SHIKI_PROVIDER and provider.name; defaults to codex.",
    )
    parser.add_argument("--steps", type=positive_int, default=None, help="Maximum Task sessions for this invocation.")
    parser.add_argument("--max-steps", type=positive_int, default=50, help="Safety cap for automatic progress.")
    parser.add_argument("--tail", default="", help="Additional bounded scope passed to the Task prompt.")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def add_provider_prompt_args(parser: argparse.ArgumentParser) -> None:
    add_common_project_args(parser)
    parser.add_argument(
        "--provider",
        choices=("codex", "claude"),
        default="",
        help="CLI Provider. Overrides SHIKI_PROVIDER and provider.name; defaults to codex.",
    )
    parser.add_argument("--tail", default="", help="Additional bounded scope passed to the prompt.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shiki", description="Install and dispatch project-local Shiki workflows.")
    parser.add_argument("--version", action="version", version=f"shiki-workflow {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install Shiki into a project and optionally initialize adapters.")
    add_common_project_args(install_parser)
    install_parser.add_argument("--source", default=DEFAULT_SOURCE, help="Git URL or local Shiki checkout to install from.")
    install_parser.add_argument("--mode", choices=["auto", "submodule", "clone", "copy"], default="auto")
    install_parser.add_argument("--ref", help="Git branch or tag for submodule/clone installs.")
    install_parser.add_argument("--tool", choices=SUPPORTED_TOOLS, default="all", help="Adapter target to install.")
    install_parser.add_argument("--skip-init", action="store_true", help="Only mount Shiki; do not initialize shiki_context/.")
    install_parser.add_argument("--skip-adapter", action="store_true", help="Initialize Shiki without installing adapter files.")
    install_parser.add_argument("--force-context", action="store_true", help="Overwrite existing context files during init.")
    install_parser.set_defaults(func=command_install)

    init_parser = subparsers.add_parser("init", help="Initialize or repair shiki_context/ from an existing shiki/.")
    add_common_project_args(init_parser)
    init_parser.add_argument("--target", help="Target directory for shiki_context/.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing context files.")
    init_parser.set_defaults(func=command_init)

    feature_parser = subparsers.add_parser("new-feature", help="Create a Shiki feature workspace.")
    add_common_project_args(feature_parser)
    feature_parser.add_argument("--taskid", "-t", required=True, help="Task id, such as FEAT-001.")
    feature_parser.set_defaults(func=command_new_feature)

    next_parser = subparsers.add_parser("next", help="Run the CLI automatic track to the configured boundary.")
    add_automatic_args(next_parser)
    next_parser.add_argument("item", nargs="?", default="", help="Optional explicit ready Plan item id.")
    next_parser.set_defaults(func=command_next)

    scan_parser = subparsers.add_parser("scan", help="Run Init through fresh Provider sessions and shared Kernel tools.")
    add_automatic_args(scan_parser)
    scan_parser.set_defaults(item="", func=command_scan)

    sync_parser = subparsers.add_parser("sync", help="Run bounded Code-to-Spec Tasks through fresh Provider sessions.")
    add_automatic_args(sync_parser)
    sync_parser.set_defaults(item="", func=command_sync)

    for name, help_text in (
        ("status", "Report current Shiki state through a fresh Provider session."),
        ("review", "Run read-only Review in a fresh Provider session."),
        ("modify", "Run one explicitly scoped modification in a fresh Provider session."),
        ("fix", "Diagnose or fix one explicitly scoped failure in a fresh Provider session."),
        ("test", "Plan or add tests in one fresh Provider session."),
        ("doctor", "Diagnose Shiki consistency in one fresh Provider session."),
        ("flow", "Produce one explicitly requested flow artifact in a fresh Provider session."),
    ):
        prompt_parser = subparsers.add_parser(name, help=help_text)
        add_provider_prompt_args(prompt_parser)
        prompt_parser.set_defaults(func=command_provider_prompt)

    task_parser = subparsers.add_parser("task", help="Use deterministic Kernel Task tools without a Provider.")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)
    task_next = task_subparsers.add_parser("next", help="Print one Task Context Envelope for Prompt manual mode.")
    add_common_project_args(task_next)
    task_next.add_argument("item", nargs="?", default="", help="Optional explicit ready Plan item id.")
    task_next.add_argument("--scope", choices=["auto", "init", "feature", "sync"], default="auto")
    task_next.set_defaults(func=command_task_next)
    task_complete = task_subparsers.add_parser("complete", help="Validate and record one Task result.")
    add_common_project_args(task_complete)
    task_complete.add_argument("task_id", help="Plan item id returned by `shiki task next`.")
    task_complete.add_argument("--output", action="append", default=[], help="Major output path; repeat as needed.")
    task_complete.add_argument("--noop", default="", help="Record an explicit no-change reason.")
    task_complete.add_argument("--scope", choices=["auto", "init", "feature", "sync"], default="auto")
    task_complete.set_defaults(func=command_task_complete)

    plan_parser = subparsers.add_parser("plan", help="Use narrow deterministic Plan mutation tools.")
    plan_subparsers = plan_parser.add_subparsers(dest="plan_command", required=True)
    plan_add = plan_subparsers.add_parser("add-item", help="Add one validated Canonical row to the active Plan.")
    add_common_project_args(plan_add)
    plan_add.add_argument("--parent", required=True, help="Current Plan task authorizing the addition.")
    plan_add.add_argument("--id", required=True, help="New Plan item id.")
    plan_add.add_argument("--phase", required=True, help="New Plan item phase.")
    plan_add.add_argument("--target", required=True, help="Feature-root-relative target or allowed marker.")
    plan_add.add_argument("--module", default="", help="Module when the Plan schema includes it.")
    plan_add.add_argument("--depends-on", default="", help="Comma-separated dependencies.")
    plan_add.add_argument("--contract", required=True, help="Canonical or Alias Contract; stored as Canonical.")
    plan_add.set_defaults(func=command_plan_add_item)

    adapter_parser = subparsers.add_parser("adapter", help="Manage project-local tool adapters.")
    adapter_subparsers = adapter_parser.add_subparsers(dest="adapter_command", required=True)
    adapter_install = adapter_subparsers.add_parser("install", help="Install project-local adapter command files.")
    add_common_project_args(adapter_install)
    adapter_install.add_argument("--tool", choices=SUPPORTED_TOOLS, required=True)
    adapter_install.add_argument("--dry-run", action="store_true", help="Print the install plan without writing files.")
    adapter_install.set_defaults(func=command_adapter_install)

    tool_parser = subparsers.add_parser("tool", help="Run Shiki-bundled deterministic tools.")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command", required=True)
    codebomb_parser = tool_subparsers.add_parser("codebomb", help="Start the Codebomb Java diagram MCP server.")
    add_common_project_args(codebomb_parser)
    codebomb_parser.add_argument("--repo", required=True, help="Local Java/Spring repository root.")
    codebomb_parser.set_defaults(func=command_tool_codebomb)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except CliError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
