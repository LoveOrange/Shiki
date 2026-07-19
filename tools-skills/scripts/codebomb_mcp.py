#!/usr/bin/env python3
"""Start the Codebomb MCP server without the Shiki CLI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SERVER = Path(__file__).resolve().with_name("codebomb.py")


def venv_python(root: Path) -> Path | None:
    for relative in [
        ".shiki/tools/codebomb/venv/bin/python",
        ".shiki/tools/codebomb/venv/Scripts/python.exe",
    ]:
        candidate = root / relative
        if candidate.is_file():
            return candidate.resolve()
    return None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Codebomb's stdio MCP server.")
    parser.add_argument("--repo", required=True, help="Local Java/Spring repository root.")
    parser.add_argument(
        "--python",
        help="Python executable with Codebomb dependencies. Defaults to .shiki/tools/codebomb/venv/bin/python.",
    )
    parser.add_argument(
        "--server",
        default=str(DEFAULT_SERVER),
        help="Path to codebomb.py. Defaults to the script next to this launcher.",
    )
    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).expanduser().resolve()
    server = Path(args.server).expanduser().resolve()
    python = Path(args.python).expanduser().resolve() if args.python else venv_python(ROOT)

    if not repo.is_dir():
        return fail(f"repo does not exist: {repo}")
    if not server.is_file():
        return fail(f"codebomb server script does not exist: {server}")
    if python is None:
        return fail("Codebomb venv python not found. Run tools-skills/scripts/install_codebomb_deps.py install first.")
    if not python.is_file():
        return fail(f"python executable does not exist: {python}")

    os.execv(str(python), [str(python), str(server), "--repo", str(repo)])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
