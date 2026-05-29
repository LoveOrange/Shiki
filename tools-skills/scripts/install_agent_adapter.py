#!/usr/bin/env python3
"""
Install project-local Shiki adapter command files for supported coding tools.

The installer writes only Shiki-owned command files and adapter metadata. It is
safe to run repeatedly; files with the Shiki managed marker are updated, matching
files are skipped, and user-owned files are reported as blocked.
"""

import argparse
import json
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
        "description": "Initialize or repair the project-local Shiki context scaffold.",
        "loads": [
            "shiki.config.yaml",
            "tools-skills/scripts/init.py",
            "core-kernel/templates/workspace/.gitignore",
            "tech-stacks/tech-contracts/",
        ],
        "body": [
            "Run the initialization flow described by the adapter contract.",
            "Use the deterministic init script when writes are needed.",
            "Stop before overwriting existing user files.",
        ],
    },
    {
        "name": "shiki-status",
        "canonical": "/shiki-status",
        "description": "Report current Shiki plan state without changing files.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
        ],
        "body": [
            "Read active_task.md and the current plan.",
            "Report the next runnable item, gate status, blockers, and missing files.",
            "Do not edit files.",
        ],
    },
    {
        "name": "shiki-next",
        "canonical": "/shiki-next",
        "description": "Execute the next allowed Shiki plan work through Core Kernel contracts.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            "core-kernel/workflows/runner/next.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
            "selected core-kernel/runtime/task_contracts/**/*.yaml",
        ],
        "body": [
            "Select the first ready item from the current plan.",
            "Load its task contract before loading workflow text.",
            "Execute only the selected Core Kernel workflow unless the adapter contract explicitly permits a bounded internal mode.",
            "Update output_files only after verification passes.",
        ],
    },
    {
        "name": "shiki-modify",
        "canonical": "/shiki-modify <target>",
        "description": "Make a bounded user-requested change to existing code or specs.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
            "direct specs and source files related to the target",
        ],
        "body": [
            "Use the supplied target and requested change from the user arguments.",
            "Determine whether the change is code-only, spec-only, or affects downstream items.",
            "Edit only the required files and mark downstream completed items STALE when affected.",
            "Run the smallest meaningful verification.",
        ],
        "requires_args": True,
    },
    {
        "name": "shiki-review",
        "canonical": "/shiki-review",
        "description": "Review produced files and implementation alignment without changing files.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
            "relevant L2 AS-IS leaf specs",
            "relevant changed source or spec files",
        ],
        "body": [
            "Review the selected scope or current diff.",
            "Output findings first, ordered by severity.",
            "Do not edit files unless the user changes the task.",
        ],
    },
    {
        "name": "shiki-sync",
        "canonical": "/shiki-sync",
        "description": "Plan and apply bounded Code -> Spec synchronization.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            "core-kernel/runtime/task_contracts/sync/plan.yaml",
            "core-kernel/runtime/task_contracts/sync/apply_leaf.yaml",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
        ],
        "body": [
            "Use only the user-specified changed source files, module, feature, or git diff scope.",
            "First create or update shiki_context/workspace/sync_plan.md.",
            "Then update at most one target leaf spec from direct source evidence.",
            "Mark ambiguous mappings MANUAL_DECISION.",
        ],
    },
    {
        "name": "shiki-doctor",
        "canonical": "/shiki-doctor",
        "description": "Diagnose or repair Shiki context structure.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            "core-kernel/runtime/task_contracts/doctor/plan.yaml",
            "core-kernel/runtime/task_contracts/doctor/apply_item.yaml",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
        ],
        "body": [
            "Diagnose read-only by default.",
            "After explicit confirmation, create shiki_context/workspace/doctor_plan.md.",
            "Repair at most one deterministic item and report unresolved BLOCKED or MANUAL_DECISION state.",
        ],
    },
]


TOOL_SPECS = {
    "codex": {
        "manifest_tool": "codex",
        "command_dir": ".codex/prompts",
        "extension": ".md",
        "format": "markdown",
        "arg_token": "$ARGUMENTS",
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": True,
            "supports_subagents": False,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item"],
    },
    "claude": {
        "manifest_tool": "claude-code",
        "command_dir": ".claude/commands",
        "extension": ".md",
        "format": "markdown",
        "arg_token": "$ARGUMENTS",
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": False,
            "supports_subagents": True,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch", "phase_wave", "subagent_delegation"],
    },
    "gemini": {
        "manifest_tool": "gemini-cli",
        "command_dir": ".gemini/commands",
        "extension": ".toml",
        "format": "gemini_toml",
        "arg_token": "{{args}}",
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": False,
            "supports_subagents": False,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch"],
    },
    "opencode": {
        "manifest_tool": "opencode",
        "command_dir": ".opencode/commands",
        "extension": ".md",
        "format": "opencode_markdown",
        "arg_token": "$ARGUMENTS",
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": True,
            "supports_subagents": True,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch", "phase_wave", "subagent_delegation"],
    },
}


@dataclass
class InstallReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    def extend(self, other: "InstallReport") -> None:
        self.created.extend(other.created)
        self.updated.extend(other.updated)
        self.skipped.extend(other.skipped)
        self.blocked.extend(other.blocked)


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
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def relative_source_root(shiki_root: Path, project_root: Path) -> str:
    try:
        value = shiki_root.relative_to(project_root).as_posix()
    except ValueError:
        value = str(shiki_root)
    return value if value else "."


def command_prompt(command: dict, source_root: str, arg_token: str) -> str:
    load_lines = [f"- {source_root}/{CONTRACT_PATH}"]
    for ref in command["loads"]:
        if ref.startswith(CONTEXT_ROOT) or ref.startswith("shiki.config.yaml") or ref.startswith("current ") or ref.startswith("direct ") or ref.startswith("relevant ") or ref.startswith("selected "):
            load_lines.append(f"- {ref}")
        else:
            load_lines.append(f"- {source_root}/{ref}")

    body_lines = "\n".join(f"{index}. {line}" for index, line in enumerate(command["body"], start=1))
    args = f"\nUser arguments: {arg_token}\n" if command.get("requires_args") else ""
    return (
        f"Use Shiki adapter command {command['canonical']}.\n\n"
        "Load:\n"
        + "\n".join(load_lines)
        + "\n\n"
        "Rules:\n"
        "- Follow Shiki Tool Adapter Contract v1.\n"
        "- Treat Shiki Core Kernel as the source of truth for plan routing, task contracts, workflow binding, context loading, evidence, and gate state.\n"
        "- Report BLOCKED, MANUAL_DECISION, and VERIFICATION_FAILED using the adapter contract fields.\n"
        + args
        + "\nSteps:\n"
        + body_lines
        + "\n"
    )


def markdown_content(tool: str, command: dict, source_root: str, arg_token: str, frontmatter: bool) -> str:
    marker = f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool}; command={command['canonical']} -->"
    prompt = command_prompt(command, source_root, arg_token)
    if frontmatter:
        return (
            "---\n"
            f"description: {command['description']}\n"
            "---\n"
            f"{marker}\n\n"
            f"{prompt}"
        )
    return f"{marker}\n\n{prompt}"


def gemini_toml_content(tool: str, command: dict, source_root: str, arg_token: str) -> str:
    prompt = command_prompt(command, source_root, arg_token)
    return (
        f"# {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool}; command={command['canonical']}\n"
        f"description = {json.dumps(command['description'])}\n"
        'prompt = """\n'
        f"{prompt}"
        '"""\n'
    )


def manifest_content(tool_key: str, spec: dict, source_root: str) -> str:
    data = {
        "managed_by": MANAGED_MARKER,
        "adapter_contract_version": CONTRACT_VERSION,
        "tool": spec["manifest_tool"],
        "source_root": source_root,
        "context_root": CONTEXT_ROOT,
        "capabilities": spec["capabilities"],
        "execution_modes": spec["execution_modes"],
        "installed_commands": [command["canonical"] for command in COMMANDS],
        "command_files": [
            f"{spec['command_dir']}/{command['name']}{spec['extension']}" for command in COMMANDS
        ],
        "adapter_key": tool_key,
    }
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def render_command_file(tool_key: str, spec: dict, command: dict, source_root: str) -> str:
    if spec["format"] == "gemini_toml":
        return gemini_toml_content(tool_key, command, source_root, spec["arg_token"])
    if spec["format"] == "opencode_markdown":
        return markdown_content(tool_key, command, source_root, spec["arg_token"], frontmatter=True)
    return markdown_content(tool_key, command, source_root, spec["arg_token"], frontmatter=False)


def write_managed_file(path: Path, content: str, project_root: Path, report: InstallReport, dry_run: bool) -> None:
    resolved_path = path.resolve()
    if not is_relative_to(resolved_path, project_root):
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
        if not dry_run:
            path.write_text(content, encoding="utf-8")
        return

    report.created.append(display)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def install_tool(tool_key: str, project_root: Path, source_root: str, dry_run: bool) -> InstallReport:
    spec = TOOL_SPECS[tool_key]
    report = InstallReport()
    manifest_path = project_root / ".shiki" / "adapters" / tool_key / "manifest.json"
    write_managed_file(
        manifest_path,
        manifest_content(tool_key, spec, source_root),
        project_root,
        report,
        dry_run,
    )

    command_dir = project_root / spec["command_dir"]
    for command in COMMANDS:
        path = command_dir / f"{command['name']}{spec['extension']}"
        write_managed_file(
            path,
            render_command_file(tool_key, spec, command, source_root),
            project_root,
            report,
            dry_run,
        )
    return report


def selected_tools(tool: str) -> list[str]:
    if tool == "all":
        return ["codex", "claude", "gemini", "opencode"]
    return [tool]


def print_report(project_root: Path, tools: list[str], report: InstallReport, dry_run: bool) -> None:
    action = "Adapter Install Plan" if dry_run else "Adapter Install"
    print("")
    print("=" * 55)
    print(f"  Shiki {action}")
    print("=" * 55)
    print(f"  Project root: {project_root}")
    print(f"  Tools: {', '.join(tools)}")

    sections = [
        ("Created" if not dry_run else "Would create", report.created, "+"),
        ("Updated" if not dry_run else "Would update", report.updated, "*"),
        ("Skipped", report.skipped, "~"),
        ("Blocked", report.blocked, "!"),
    ]
    for title, values, marker in sections:
        print(f"\n  {title} ({len(values)} files):")
        for value in values:
            print(f"    {marker} {value}")

    print("")
    if report.blocked:
        print("  Result: blocked; no user-owned file was overwritten.")
    elif dry_run:
        print("  Result: plan only; no files were written.")
    else:
        print("  Result: adapter files installed.")
    print("=" * 55)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install project-local Shiki adapter command files."
    )
    parser.add_argument(
        "--tool",
        choices=["codex", "claude", "gemini", "opencode", "all"],
        required=True,
        help="Adapter target to install.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root to install into. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the install plan without writing files.",
    )
    parser.add_argument(
        "--allow-outside-project",
        action="store_true",
        help="Allow --project-root outside the current working directory.",
    )
    args = parser.parse_args()

    cwd = Path.cwd().resolve()
    project_root = Path(args.project_root).resolve()
    if not args.allow_outside_project and not is_relative_to(project_root, cwd):
        print(f"ERROR: refusing to write outside the current project: {project_root}", file=sys.stderr)
        print("       Re-run with --allow-outside-project if this is intentional.", file=sys.stderr)
        return 2

    shiki_root = get_shiki_root()
    source_root = relative_source_root(shiki_root, project_root)
    tools = selected_tools(args.tool)
    combined = InstallReport()
    for tool in tools:
        combined.extend(install_tool(tool, project_root, source_root, args.dry_run))

    print_report(project_root, tools, combined, args.dry_run)
    return 1 if combined.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
