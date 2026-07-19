#!/usr/bin/env python3
"""Install project-local Shiki Prompt-track adapters.

Generated prompts are deliberately thin: the Core Kernel selects and prepares
one Task, while the developer's current Coding Agent session executes it.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


CONTRACT_VERSION = "v1"
MANAGED_MARKER = "Shiki Adapter: managed by tools-skills/scripts/install_agent_adapter.py"
CONTRACT_PATH = "user-interface/adapters/tool_adapter_contract_v1.md"
CONTEXT_ROOT = "shiki_context"


COMMANDS = [
    {
        "name": "shiki-init",
        "canonical": "/shiki-init",
        "description": "Initialize or repair the project-local Shiki scaffold.",
        "instructions": [
            "Run `python <source-root>/tools-skills/scripts/init.py`.",
            "Report files created, skipped, or blocked; never overwrite user-owned files.",
            "Stop after initialization.",
        ],
    },
    {
        "name": "shiki-scan",
        "canonical": "/shiki-scan",
        "description": "Execute one Init baseline Task in the current session.",
        "instructions": [
            "If `shiki_context/workspace/_plan.md` has no Task rows, run `python <source-root>/tools-skills/scripts/scan.py` once to seed the Init Plan.",
            "Run `shiki task next` and treat its Context Envelope as the complete authority for this Task.",
            "Execute exactly that one Task in this current Coding Agent session.",
            "On PASS, run the returned `shiki task complete ...` command with every produced output; use `--noop <reason>` only when the contract permits no file output.",
            "Stop and return control. Do not execute another Task or trigger Review automatically.",
        ],
    },
    {
        "name": "shiki-new-feature",
        "canonical": "/shiki-new-feature <taskid>",
        "description": "Create a new Shiki feature workspace.",
        "requires_args": True,
        "instructions": [
            "Require a task id from the invocation arguments.",
            "Run `python <source-root>/tools-skills/scripts/new_feature.py --taskid <taskid>`.",
            "Stop after the feature workspace is created.",
        ],
    },
    {
        "name": "shiki-status",
        "canonical": "/shiki-status",
        "description": "Report current Shiki scope and Plan state without edits.",
        "instructions": [
            "Read `shiki_context/workspace/active_task.md` and the active scope `_plan.md`.",
            "Report the next Task candidate, blockers, and missing artifacts.",
            "Do not change files or Plan state.",
        ],
    },
    {
        "name": "shiki-next",
        "canonical": "/shiki-next [item]",
        "description": "Execute exactly one Kernel-selected Task in the current session.",
        "instructions": [
            "Run `shiki task next [item]` and treat its Context Envelope as the complete authority for this Task.",
            "Execute exactly that one Task in this current Coding Agent session.",
            "On PASS, run the returned `shiki task complete ...` command with every produced output; use `--noop <reason>` only when the contract permits no file output.",
            "On BLOCKED, FAILED, or MANUAL_DECISION, do not write completion state.",
            "Stop and return control. Do not batch Tasks, open a fresh session, or trigger Review automatically.",
        ],
    },
    {
        "name": "shiki-apply",
        "canonical": "/shiki-apply [item]",
        "description": "Compatibility alias for the Prompt-track single-Task flow.",
        "instructions": [
            "Use the same one-Task current-session flow as `/shiki-next`.",
            "State that the compatibility entry was used.",
        ],
    },
    {
        "name": "shiki-modify",
        "canonical": "/shiki-modify <target>",
        "description": "Make a bounded requested change to an existing target.",
        "requires_args": True,
        "instructions": [
            "Use the invocation arguments as the target and requested change.",
            "Load only directly relevant specs and source files, make the smallest change, and run proportional verification.",
            "Do not invent or bypass Shiki Plan completion state.",
        ],
    },
    {
        "name": "shiki-review",
        "canonical": "/shiki-review [scope]",
        "description": "Run developer-requested Review without changing files.",
        "instructions": [
            "Review the requested scope or current diff against its direct specifications.",
            "Return PASS, CHANGE_REQUEST, BLOCKED, FAILED, or MANUAL_DECISION on the first line.",
            "List findings by severity. Do not edit files.",
        ],
    },
    {
        "name": "shiki-sync",
        "canonical": "/shiki-sync",
        "description": "Execute one bounded Code-to-Spec synchronization Task.",
        "instructions": [
            "Run `shiki task next --scope sync`, execute exactly the returned Sync Task, and use the returned scope-aware `shiki task complete` command only on PASS.",
            "Stop after one Task; later Sync Tasks require another developer invocation.",
        ],
    },
    {
        "name": "shiki-doctor",
        "canonical": "/shiki-doctor",
        "description": "Execute one bounded Shiki consistency Task.",
        "instructions": [
            "Read the active scope plus the Doctor planning Contract and workflow.",
            "Diagnose consistency problems without editing files or Plan state.",
            "Return a status-first bounded repair recommendation; use `/shiki-fix` only after explicit developer authorization.",
        ],
    },
    {
        "name": "shiki-fix",
        "canonical": "/shiki-fix <finding>",
        "description": "Fix one explicit Review or Doctor finding.",
        "requires_args": True,
        "instructions": [
            "Use the invocation arguments as the only authorized finding.",
            "Make the smallest correction and run the directly relevant verification.",
            "Do not mark unrelated Plan Tasks complete.",
        ],
    },
    {
        "name": "shiki-web-spec",
        "canonical": "/shiki-web-spec <url-or-target>",
        "description": "Capture a bounded web-facing specification.",
        "requires_args": True,
        "instructions": [
            "Use the invocation arguments as the target.",
            "Follow the current Shiki task contract when one is active; otherwise produce only the requested specification.",
            "Do not update Plan completion state without a Kernel-prepared Task.",
        ],
    },
]


TOOL_SPECS = {
    "codex": {
        "label": "Codex",
        "adapter": "user-interface/adapters/codex_adapter.md",
        "command_dir": ".codex/prompts",
        "extension": ".md",
        "skill_files": [".codex/skills/shiki/SKILL.md"],
    },
    "claude": {
        "label": "Claude Code",
        "adapter": "user-interface/adapters/claude_code_adapter.md",
        "command_dir": ".claude/commands",
        "extension": ".md",
        "obsolete_files": [".claude/agents/shiki-phase-wave.md"],
    },
    "gemini": {
        "label": "Gemini CLI",
        "adapter": "user-interface/adapters/gemini_cli_adapter.md",
        "command_dir": ".gemini/commands",
        "extension": ".toml",
    },
    "opencode": {
        "label": "OpenCode",
        "adapter": "user-interface/adapters/opencode_adapter.md",
        "command_dir": ".opencode/commands",
        "extension": ".md",
        "agent_files": [
            ".opencode/agents/shiki-runner.md",
            ".opencode/agents/shiki-reviewer.md",
        ],
        "obsolete_files": [".opencode/agents/shiki-phase-wave.md"],
    },
}


@dataclass
class InstallReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    def extend(self, other: "InstallReport") -> None:
        for name in ("created", "updated", "removed", "skipped", "blocked"):
            getattr(self, name).extend(getattr(other, name))


def get_shiki_root() -> Path:
    return Path(__file__).resolve().parents[2]


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def relative_source_root(shiki_root: Path, project_root: Path) -> str:
    return Path(os.path.relpath(shiki_root, project_root)).as_posix()


def substitute_source_root(line: str, source_root: str) -> str:
    return line.replace("<source-root>", source_root)


def command_prompt(command: dict, source_root: str, adapter_path: str, arg_token: str) -> str:
    args = arg_token.strip()
    lines = [
        f"# {command['canonical']}",
        "",
        f"{command['description']}",
        "",
        "This is the Shiki Prompt track. The developer owns this Coding Agent session and Review timing.",
        "",
        "Before acting, read:",
        f"- `{source_root}/{CONTRACT_PATH}`",
        f"- `{source_root}/{adapter_path}`",
        f"- `{source_root}/core-kernel/runtime/execution_session.md`",
    ]
    if command["name"] in {"shiki-next", "shiki-apply", "shiki-scan", "shiki-sync", "shiki-doctor"}:
        lines.append(f"- `{source_root}/core-kernel/workflows/runner/next.md`")
    lines.extend(["", "Instructions:"])
    lines.extend(f"- {substitute_source_root(item, source_root)}" for item in command["instructions"])
    if command.get("requires_args"):
        lines.extend(["", f"Invocation arguments: `{args or '<missing>'}`"])
    elif args:
        lines.extend(["", f"Optional invocation arguments: `{args}`"])
    return "\n".join(lines).rstrip() + "\n"


def markdown_content(tool_key: str, command: dict, source_root: str) -> str:
    spec = TOOL_SPECS[tool_key]
    arg_token = "$ARGUMENTS"
    prompt = command_prompt(command, source_root, spec["adapter"], arg_token)
    return (
        "---\n"
        f"description: {command['description']}\n"
        "---\n"
        f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool_key}; command={command['name']} -->\n\n"
        f"{prompt}"
    )


def gemini_content(command: dict, source_root: str) -> str:
    prompt = command_prompt(command, source_root, TOOL_SPECS["gemini"]["adapter"], "{{args}}")
    escaped_description = command["description"].replace('"', '\\"')
    return (
        f"# {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=gemini; command={command['name']}\n"
        f'description = "{escaped_description}"\n'
        "prompt = '''\n"
        f"{prompt}"
        "'''\n"
    )


def manifest_content(tool_key: str, source_root: str) -> str:
    spec = TOOL_SPECS[tool_key]
    payload = {
        "managed_by": MANAGED_MARKER,
        "contract_version": CONTRACT_VERSION,
        "tool": tool_key,
        "tool_label": spec["label"],
        "source_root": source_root,
        "adapter_contract": f"{source_root}/{CONTRACT_PATH}",
        "adapter_reference": f"{source_root}/{spec['adapter']}",
        "collaboration_track": "prompt_manual",
        "execution_modes": ["single_task_current_session"],
        "session_owner": "developer",
        "review_owner": "developer",
        "commands": [command["canonical"] for command in COMMANDS],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def codex_skill_content(source_root: str) -> str:
    commands = "\n".join(f"- `{item['canonical']}` — {item['description']}" for item in COMMANDS)
    return (
        "---\n"
        "name: shiki\n"
        "description: Use Shiki's Prompt track to execute one Kernel-prepared Task in the current Codex session.\n"
        "---\n"
        f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=codex; skill=shiki -->\n\n"
        "# Shiki\n\n"
        f"Read `{source_root}/{CONTRACT_PATH}` and `{source_root}/{TOOL_SPECS['codex']['adapter']}` first.\n\n"
        "The Kernel owns routing, context preparation, and completion bookkeeping. Execute at most one prepared Task per invocation in the current session. Review runs only when the developer requests it.\n\n"
        "## Commands\n\n"
        f"{commands}\n"
    )


def opencode_agent_content(name: str, source_root: str) -> str:
    reviewer = name == "shiki-reviewer"
    mode = "subagent" if reviewer else "primary"
    description = "Read-only Shiki reviewer." if reviewer else "Shiki Prompt-track single-Task runner."
    instructions = (
        "Review only the assigned files and return a status-first result. Do not edit files or Plan state."
        if reviewer
        else "Use Kernel task tools and execute exactly one prepared Task in the current session. Do not batch or trigger Review automatically."
    )
    return (
        "---\n"
        f"description: {description}\n"
        f"mode: {mode}\n"
        "---\n"
        f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=opencode; agent={name} -->\n\n"
        f"Read `{source_root}/{CONTRACT_PATH}` and `{source_root}/{TOOL_SPECS['opencode']['adapter']}`.\n\n"
        f"{instructions}\n"
    )


def write_managed_file(path: Path, content: str, project_root: Path, report: InstallReport, dry_run: bool) -> None:
    if not is_relative_to(path.resolve(), project_root):
        report.blocked.append(f"{display_path(path, project_root)} (outside project root)")
        return
    display = display_path(path, project_root)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            report.skipped.append(display)
            return
        if MANAGED_MARKER not in existing:
            report.blocked.append(f"{display} (existing file is not Shiki-managed)")
            return
        report.updated.append(display)
    else:
        report.created.append(display)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def remove_obsolete_file(path: Path, project_root: Path, report: InstallReport, dry_run: bool) -> None:
    if not path.exists():
        return
    display = display_path(path, project_root)
    if MANAGED_MARKER not in path.read_text(encoding="utf-8"):
        report.blocked.append(f"{display} (obsolete file is not Shiki-managed)")
        return
    report.removed.append(display)
    if not dry_run:
        path.unlink()


def install_tool(tool_key: str, project_root: Path, source_root: str, dry_run: bool) -> InstallReport:
    spec = TOOL_SPECS[tool_key]
    report = InstallReport()
    write_managed_file(
        project_root / ".shiki" / "adapters" / tool_key / "manifest.json",
        manifest_content(tool_key, source_root),
        project_root,
        report,
        dry_run,
    )
    for command in COMMANDS:
        path = project_root / spec["command_dir"] / f"{command['name']}{spec['extension']}"
        content = gemini_content(command, source_root) if tool_key == "gemini" else markdown_content(tool_key, command, source_root)
        write_managed_file(path, content, project_root, report, dry_run)
    if tool_key == "codex":
        for relative in spec.get("skill_files", []):
            write_managed_file(project_root / relative, codex_skill_content(source_root), project_root, report, dry_run)
    if tool_key == "opencode":
        for relative in spec.get("agent_files", []):
            write_managed_file(project_root / relative, opencode_agent_content(Path(relative).stem, source_root), project_root, report, dry_run)
    for relative in spec.get("obsolete_files", []):
        remove_obsolete_file(project_root / relative, project_root, report, dry_run)
    return report


def print_report(project_root: Path, tools: list[str], report: InstallReport, dry_run: bool) -> None:
    print(f"Shiki {'Adapter Install Plan' if dry_run else 'Adapter Install'}")
    print(f"Project root: {project_root}")
    print(f"Tools: {', '.join(tools)}")
    for title, values in (
        ("Created" if not dry_run else "Would create", report.created),
        ("Updated" if not dry_run else "Would update", report.updated),
        ("Removed" if not dry_run else "Would remove", report.removed),
        ("Skipped", report.skipped),
        ("Blocked", report.blocked),
    ):
        print(f"{title} ({len(values)}):")
        for value in values:
            print(f"  {value}")
    if report.blocked:
        print("Result: blocked; no user-owned file was overwritten.")
    elif dry_run:
        print("Result: plan only; no files were written.")
    else:
        print("Result: adapter files installed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install project-local Shiki Prompt-track adapters.")
    parser.add_argument("--tool", choices=[*TOOL_SPECS, "all"], required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-outside-project", action="store_true")
    args = parser.parse_args()

    cwd = Path.cwd().resolve()
    project_root = Path(args.project_root).resolve()
    if not args.allow_outside_project and not is_relative_to(project_root, cwd):
        print(f"ERROR: refusing to write outside the current project: {project_root}", file=sys.stderr)
        return 2

    source_root = relative_source_root(get_shiki_root(), project_root)
    tools = list(TOOL_SPECS) if args.tool == "all" else [args.tool]
    report = InstallReport()
    for tool in tools:
        report.extend(install_tool(tool, project_root, source_root, args.dry_run))
    print_report(project_root, tools, report, args.dry_run)
    return 1 if report.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
