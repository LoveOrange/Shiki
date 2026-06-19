"""Console entrypoint for installing and dispatching Shiki helpers."""

from __future__ import annotations

import argparse
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


def add_common_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Consumer project root. Defaults to the current directory.")
    parser.add_argument("--shiki-dir", default=DEFAULT_SHIKI_DIR, help="Project-local Shiki directory. Defaults to shiki/.")


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

    adapter_parser = subparsers.add_parser("adapter", help="Manage project-local tool adapters.")
    adapter_subparsers = adapter_parser.add_subparsers(dest="adapter_command", required=True)
    adapter_install = adapter_subparsers.add_parser("install", help="Install project-local adapter command files.")
    add_common_project_args(adapter_install)
    adapter_install.add_argument("--tool", choices=SUPPORTED_TOOLS, required=True)
    adapter_install.add_argument("--dry-run", action="store_true", help="Print the install plan without writing files.")
    adapter_install.set_defaults(func=command_adapter_install)

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
