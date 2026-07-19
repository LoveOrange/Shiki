#!/usr/bin/env python3
"""Install Codebomb dependencies into an isolated project-local venv."""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = Path(__file__).resolve().with_name("codebomb_requirements.txt")
DEFAULT_WHEELHOUSE = "vendor/codebomb-wheels"
DEFAULT_VENV = ".shiki/tools/codebomb/venv"


def run(cmd: list[str], cwd: Path) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def resolve_project_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"ERROR: project root does not exist: {root}")
    return root


def resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def venv_python(venv_path: Path) -> Path:
    candidates = [
        venv_path / "bin" / "python",
        venv_path / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"ERROR: venv python not found under {venv_path}")


def command_download(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args.project_root)
    wheelhouse = resolve_path(project_root, args.wheelhouse)
    wheelhouse.mkdir(parents=True, exist_ok=True)
    run(
        [
            args.python,
            "-m",
            "pip",
            "download",
            "--dest",
            str(wheelhouse),
            "-r",
            str(REQUIREMENTS),
        ],
        cwd=project_root,
    )
    print(f"Codebomb wheelhouse ready: {wheelhouse}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args.project_root)
    wheelhouse = resolve_path(project_root, args.wheelhouse)
    if not wheelhouse.is_dir():
        raise SystemExit(f"ERROR: wheelhouse does not exist: {wheelhouse}")
    venv_path = resolve_path(project_root, args.venv)
    if not venv_path.exists():
        print(f"Creating Codebomb venv: {venv_path}")
        venv.EnvBuilder(with_pip=True).create(venv_path)
    python = venv_python(venv_path)
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "-r",
            str(REQUIREMENTS),
        ],
        cwd=project_root,
    )
    print(f"Codebomb dependencies installed: {venv_path}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args.project_root)
    venv_path = resolve_path(project_root, args.venv)
    python = venv_python(venv_path)
    run(
        [
            str(python),
            "-c",
            "import mcp, tree_sitter, tree_sitter_java; print('Codebomb dependencies OK')",
        ],
        cwd=project_root,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare isolated Codebomb dependencies.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download wheels for offline Codebomb install.")
    download.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    download.add_argument("--wheelhouse", default=DEFAULT_WHEELHOUSE, help=f"Wheel output directory. Defaults to {DEFAULT_WHEELHOUSE}.")
    download.add_argument("--python", default=sys.executable, help="Python executable used to run pip download.")
    download.set_defaults(func=command_download)

    install = subparsers.add_parser("install", help="Install Codebomb wheels into a project-local venv.")
    install.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    install.add_argument("--wheelhouse", default=DEFAULT_WHEELHOUSE, help=f"Wheel input directory. Defaults to {DEFAULT_WHEELHOUSE}.")
    install.add_argument("--venv", default=DEFAULT_VENV, help=f"Venv path. Defaults to {DEFAULT_VENV}.")
    install.set_defaults(func=command_install)

    doctor = subparsers.add_parser("doctor", help="Check the project-local Codebomb venv.")
    doctor.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    doctor.add_argument("--venv", default=DEFAULT_VENV, help=f"Venv path. Defaults to {DEFAULT_VENV}.")
    doctor.set_defaults(func=command_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
