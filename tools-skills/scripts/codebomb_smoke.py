#!/usr/bin/env python3
"""Quick local smoke test for the Codebomb MCP server."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


DEFAULT_CALLS = [
    ("sequence_audit", "codebomb.sequence_diagram", {"entry": "POST /api/audit/evaluate", "max_depth": 3}),
    ("sequence_engine", "codebomb.sequence_diagram", {"entry": "POST /api/engine/evaluate", "max_depth": 3}),
    ("class_audit_controller", "codebomb.class_diagram", {"target": "AuditController", "max_classes": 20}),
    ("class_audit_engine_impl", "codebomb.class_diagram", {"target": "AuditEngineImpl", "max_classes": 20}),
    ("component_server", "codebomb.component_diagram", {"scope": "com.cmb.server"}),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Call Codebomb MCP tools and print Mermaid diagrams.")
    parser.add_argument("--repo", required=True, help="Target Java/Spring repository root.")
    parser.add_argument(
        "--server",
        default=str(root / "tools-skills" / "scripts" / "codebomb.py"),
        help="Path to codebomb.py. Defaults to this Shiki checkout's script.",
    )
    parser.add_argument(
        "--python",
        default=str(root / ".shiki" / "tools" / "codebomb" / "venv" / "bin" / "python"),
        help="Python executable with mcp/tree-sitter deps. Defaults to .shiki/tools/codebomb/venv/bin/python.",
    )
    parser.add_argument("--output", help="Optional directory to write .mmd and .json files.")
    return parser.parse_args(argv)


def content_text(result: object) -> str:
    content = getattr(result, "content", [])
    if not content:
        raise RuntimeError("MCP tool returned no content")
    return getattr(content[0], "text")


async def run(args: argparse.Namespace) -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo = Path(args.repo).expanduser().resolve()
    server = Path(args.server).expanduser().resolve()
    python = Path(args.python).expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit(f"ERROR: repo does not exist: {repo}")
    if not server.is_file():
        raise SystemExit(f"ERROR: codebomb server script does not exist: {server}")
    if not python.is_file():
        raise SystemExit(f"ERROR: python executable does not exist: {python}")

    output = Path(args.output).expanduser().resolve() if args.output else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)

    params = StdioServerParameters(command=str(python), args=[str(server), "--repo", str(repo)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("MCP tools: " + ", ".join(tool.name for tool in tools.tools))
            for label, tool_name, arguments in DEFAULT_CALLS:
                result = await session.call_tool(tool_name, arguments)
                payload = json.loads(content_text(result))
                diagram = payload["diagram"]
                print(f"\n## {label}")
                print(f"tool={tool_name}")
                print(f"source_files={len(payload.get('source_files', []))}")
                print(f"diagram_lines={len(diagram.splitlines())}")
                print("```mermaid")
                print(diagram)
                print("```")
                if output is not None:
                    (output / f"{label}.mmd").write_text(diagram + "\n", encoding="utf-8")
                    (output / f"{label}.json").write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
