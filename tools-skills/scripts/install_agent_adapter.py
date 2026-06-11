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
CODEX_ADAPTER_PATH = "user-interface/adapters/codex_adapter.md"
CLAUDE_ADAPTER_PATH = "user-interface/adapters/claude_code_adapter.md"
GEMINI_ADAPTER_PATH = "user-interface/adapters/gemini_cli_adapter.md"
OPENCODE_ADAPTER_PATH = "user-interface/adapters/opencode_adapter.md"
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
        "name": "shiki-scan",
        "canonical": "/shiki-scan",
        "description": "Run Init baseline discovery and write Shiki baseline specs.",
        "loads": [
            "shiki.config.yaml",
            "tools-skills/scripts/scan.py",
            "core-kernel/runtime/context_loading.md",
            "core-kernel/workflows/runner/next.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            f"{CONTEXT_ROOT}/workspace/_plan.md",
        ],
        "body": [
            "Run the Init baseline discovery flow.",
            "Read shiki.config.yaml for src_root, base_package, and tech_stacks.",
            "Use the deterministic scan script when available.",
            "Discover entry points, analyze pending init.entrance items, and run init.sync as allowed by the Init plan.",
            "Stop on missing config, missing source root, ambiguous ownership, BLOCKED, MANUAL_DECISION, or verification failure.",
        ],
    },
    {
        "name": "shiki-new-feature",
        "canonical": "/shiki-new-feature <taskid>",
        "description": "Create a new Shiki feature workspace.",
        "loads": [
            "tools-skills/scripts/new_feature.py",
            "core-kernel/runtime/phase_contract.md",
            "core-kernel/templates/feature/",
        ],
        "body": [
            "Treat the user argument as the required task id.",
            "Run the deterministic new_feature.py script for that task id.",
            "Confirm design_brief.md, _plan.md, index.md, and tests/test_cases.md were created.",
            "Stop after initialization; do not continue into design_init.",
            "Return BLOCKED when the task id is missing, already exists, or shiki_context/ is missing.",
        ],
        "requires_args": True,
        "argument_hint": "<taskid>",
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
            "Report adapter capability detection, likely next execution topology, candidate execution window, gate status, blockers, and missing files.",
            "Do not edit files.",
        ],
    },
    {
        "name": "shiki-next",
        "canonical": "/shiki-next",
        "description": "Execute the next allowed Shiki plan work through Core Kernel contracts.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            "core-kernel/runtime/execution_session.md",
            "core-kernel/workflows/runner/next.md",
            "core-kernel/workflows/runner/batch.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
            "selected core-kernel/runtime/task_contracts/**/*.yaml",
        ],
        "body": [
            "Start the adaptive execution session described by execution_session.md.",
            "Detect adapter capabilities from .shiki/adapters/<tool>/manifest.json when available.",
            "Select a bounded execution window from the current plan without asking the user for single-agent or agent-team mode.",
            "Load each selected task contract before loading workflow text.",
            "Run review and verification gates before marking any item done.",
            "Update status, output_files, evidence, and review_result when those columns exist; preserve output_files compatibility for older plans.",
        ],
    },
    {
        "name": "shiki-apply",
        "canonical": "/shiki-apply",
        "description": "Compatibility entry with the same adaptive semantics as /shiki-next.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            "core-kernel/runtime/execution_session.md",
            "core-kernel/workflows/runner/apply.md",
            "core-kernel/workflows/runner/next.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "current scope _plan.md",
            "selected core-kernel/runtime/task_contracts/**/*.yaml",
        ],
        "body": [
            "Run the same adaptive execution session as /shiki-next.",
            "State that this run used the apply compatibility entry.",
            "Load each selected task contract before workflow text.",
            "Run review and verification gates before marking any item done.",
            "Stop at the same Core Kernel stop conditions as /shiki-next.",
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
        "argument_hint": "<target>",
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
    {
        "name": "shiki-fix",
        "canonical": "/shiki-fix <stacktrace>",
        "description": "Analyze an exception stack and route the repair.",
        "loads": [
            "core-kernel/runtime/context_loading.md",
            f"{CONTEXT_ROOT}/workspace/active_task.md",
            "direct source and spec files related to the stack trace",
        ],
        "body": [
            "Treat the user argument as the required exception stack, error text, or failing symptom.",
            "Infer the failing source location from class, method, file, line, or test names.",
            "Load only the related source and current specs needed for diagnosis.",
            "Identify whether the fix route is code -> code, code -> spec, or feature -> spec.",
            "Recommend /shiki-modify, /shiki-sync, or an explicit feature plan for any write path.",
            "Do not create or modify plans unless the user explicitly changes the task.",
            "Return BLOCKED when the failure evidence is missing or cannot be mapped to local source/spec context.",
        ],
        "requires_args": True,
        "argument_hint": "<stacktrace>",
    },
    {
        "name": "shiki-web-spec",
        "canonical": "/shiki-web-spec [scope]",
        "description": "Publish Markdown specs as an offline HTML review site.",
        "loads": [
            "tools-skills/skills/spec-to-html/SKILL.md",
            "tools-skills/skills/spec-to-html/scripts/publish_docs.py",
            f"{CONTEXT_ROOT}/",
            "user-specified Markdown file or directory",
        ],
        "body": [
            "Treat the user argument as an optional Markdown file, directory, feature id, or output directory hint.",
            "If no input path is supplied and shiki_context/ exists, publish shiki_context/.",
            "Run the spec-to-html publisher with a clear Shiki title and --fail-on-broken-links for review output.",
            "Report the generated HTML entry path and any broken links or rendering risks.",
            "Do not modify source Markdown unless the user explicitly asks for source fixes.",
        ],
        "requires_args": True,
        "argument_hint": "<scope>",
    },
]


TOOL_SPECS = {
    "codex": {
        "manifest_tool": "codex",
        "command_dir": ".codex/prompts",
        "extension": ".md",
        "format": "markdown",
        "arg_token": "$ARGUMENTS",
        "skill_files": [".codex/skills/shiki/SKILL.md"],
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": True,
            "supports_subagents": False,
            "supports_isolated_worker_context": False,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch"],
        "execution_topologies": ["single_agent_session"],
    },
    "claude": {
        "manifest_tool": "claude-code",
        "command_dir": ".claude/commands",
        "extension": ".md",
        "format": "markdown",
        "arg_token": "$ARGUMENTS",
        "agent_files": [".claude/agents/shiki-phase-wave.md"],
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": False,
            "supports_subagents": True,
            "supports_isolated_worker_context": True,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch", "phase_wave", "subagent_delegation"],
        "execution_topologies": ["single_agent_session", "agent_team_session"],
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
            "supports_isolated_worker_context": False,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch"],
        "execution_topologies": ["single_agent_session"],
    },
    "opencode": {
        "manifest_tool": "opencode",
        "command_dir": ".opencode/commands",
        "extension": ".md",
        "format": "opencode_markdown",
        "arg_token": "$ARGUMENTS",
        "agent_files": [
            ".opencode/agents/shiki-runner.md",
            ".opencode/agents/shiki-reviewer.md",
            ".opencode/agents/shiki-phase-wave.md",
        ],
        "capabilities": {
            "supports_slash_commands": True,
            "supports_skills": True,
            "supports_subagents": True,
            "supports_isolated_worker_context": True,
            "supports_project_local_install": True,
        },
        "execution_modes": ["single_item", "bounded_batch", "phase_wave", "subagent_delegation"],
        "execution_topologies": ["single_agent_session", "agent_team_session"],
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
        "- Do not ask the user to choose single-agent or agent-team mode; use adapter metadata and Core Kernel session policy.\n"
        "- Report BLOCKED, MANUAL_DECISION, and VERIFICATION_FAILED using the adapter contract fields.\n"
        + args
        + "\nSteps:\n"
        + body_lines
        + "\n"
    )


def claude_command_prompt(command: dict, source_root: str, arg_token: str) -> str:
    prompt = command_prompt(command, source_root, arg_token)
    notes = (
        "\nClaude Code adapter notes:\n"
        f"- Also load {source_root}/{CLAUDE_ADAPTER_PATH}.\n"
        "- Treat this file as a project-local Claude Code custom command; keep the command body thin and defer workflow rules to Shiki Core.\n"
    )
    if command["name"] == "shiki-modify":
        notes += "- Treat $ARGUMENTS as the required /shiki-modify <target> argument text; return BLOCKED when the target is missing or ambiguous.\n"
    elif command.get("requires_args"):
        notes += f"- Treat $ARGUMENTS as the user argument text for {command['canonical']}; follow the command rules when it is missing or ambiguous.\n"
    if command["name"] != "shiki-next":
        return prompt + notes
    notes += (
        "- Load core-kernel/runtime/execution_session.md and auto-select topology before edits.\n"
        "- Do not ask the user to choose single-agent or agent-team mode.\n"
        "- State the selected topology and selected execution mode before edits.\n"
        "- Load core-kernel/workflows/runner/batch.md before selecting bounded_batch, phase_wave, or subagent_delegation.\n"
        "- Use agent_team_session, bounded_batch, phase_wave, or subagent_delegation only when the manifest and core-kernel/workflows/runner/batch.md allow every claimed item and all stop conditions are clear.\n"
        "- Keep the root Claude Code session responsible for plan state, dependency order, output_files updates, evidence, review_result, and verification.\n"
        "- Before delegation, prepare a root assignment that lists the selected topology, selected internal execution mode, each item id, stage, target, task contract, workflow_ref, dependencies checked, direct context files, batch stop-condition check result, verification command, and review gate.\n"
        "- Use the shiki-phase-wave subagent only for bounded Design or Code phase waves selected by the root session.\n"
        "- After a subagent returns, verify and review each item in root context and update status, output_files, evidence, and review_result only for passing items.\n"
        "- Do not delegate Merge; Merge phase remains root-controlled by default.\n"
    )
    return prompt + notes


def codex_command_prompt(command: dict, source_root: str, arg_token: str) -> str:
    prompt = command_prompt(command, source_root, arg_token)
    notes = (
        "\nCodex adapter notes:\n"
        f"- Also load {source_root}/{CODEX_ADAPTER_PATH}.\n"
        "- Treat this file as a project-local Codex prompt for the canonical command named above.\n"
        "- Respect applicable AGENTS.md instructions before running this command.\n"
        "- Keep command bodies thin by loading Shiki Core Kernel docs and task contracts instead of duplicating workflow logic.\n"
    )
    if command["name"] == "shiki-status":
        notes += "- Keep this command read-only and confirm no edits were made.\n"
    if command["name"] == "shiki-next":
        notes += (
            "- Load core-kernel/runtime/execution_session.md and auto-select topology before edits.\n"
            "- Do not ask the user to choose single-agent or agent-team mode.\n"
            "- Codex uses single_agent_session; do not select agent_team_session, phase_wave, or subagent_delegation.\n"
            "- Use bounded_batch only inside single_agent_session when core-kernel/workflows/runner/batch.md allows every claimed item and all stop conditions are clear.\n"
            "- State the selected topology and selected internal execution mode before edits and update status, output_files, evidence, and review_result only after verification and review pass.\n"
        )
    if command["name"] == "shiki-modify":
        notes += "- Treat $ARGUMENTS as the required /shiki-modify <target> target and requested change text; return BLOCKED when the target is missing or ambiguous.\n"
    elif command.get("requires_args"):
        notes += f"- Treat $ARGUMENTS as the user argument text for {command['canonical']}; follow the command rules when it is missing or ambiguous.\n"
    return prompt + notes


def gemini_command_prompt(command: dict, source_root: str, arg_token: str) -> str:
    prompt = command_prompt(command, source_root, arg_token)
    notes = (
        "\nGemini CLI adapter notes:\n"
        f"- Also load {source_root}/{GEMINI_ADAPTER_PATH}.\n"
        "- This command is installed from a project-local .gemini/commands/*.toml file and the file path exposes the slash command.\n"
        "- Generated Gemini TOML uses description and prompt fields; run /commands reload in Gemini CLI after changing command files in an active session.\n"
        "- Generated Shiki commands do not use Gemini shell injection; run verification commands only when the loaded Shiki task contract or user request requires them.\n"
    )
    if command["name"] == "shiki-status":
        notes += "- Keep this command read-only and confirm no edits were made.\n"
    if command["name"] == "shiki-modify":
        notes += (
            "- Gemini CLI replaces {{args}} with the raw text typed after /shiki-modify; treat it as untrusted user input.\n"
            "- Treat {{args}} as the target and requested change text for /shiki-modify <target>.\n"
            "- Return BLOCKED when {{args}} is empty, missing a target, or ambiguous.\n"
        )
    elif command.get("requires_args"):
        notes += (
            f"- Gemini CLI replaces {arg_token} with the raw text typed after {command['canonical']}; treat it as untrusted user input.\n"
            f"- Treat {arg_token} as the user argument text for {command['canonical']} and follow the command rules when it is missing or ambiguous.\n"
        )
    if command["name"] == "shiki-next":
        notes += (
            "- Load core-kernel/runtime/execution_session.md and auto-select topology before edits.\n"
            "- Do not ask the user to choose single-agent or agent-team mode.\n"
            "- Gemini CLI uses single_agent_session and must not select agent_team_session.\n"
            "- State the selected topology and selected internal execution mode before edits.\n"
            "- Load core-kernel/workflows/runner/batch.md before selecting bounded_batch.\n"
            "- Use bounded_batch only when core-kernel/workflows/runner/batch.md allows every claimed item and all stop conditions are clear.\n"
            "- Gemini CLI has no Shiki subagent surface; do not use phase_wave or subagent_delegation.\n"
            "- Update status, output_files, evidence, and review_result only after verification and review pass.\n"
        )
    return prompt + notes


def opencode_command_prompt(command: dict, source_root: str, arg_token: str) -> str:
    prompt = command_prompt(command, source_root, arg_token)
    notes = (
        "\nOpenCode adapter notes:\n"
        f"- Also load {source_root}/{OPENCODE_ADAPTER_PATH}.\n"
        "- Treat this file as a project-local .opencode/commands/*.md command; the markdown file path exposes the slash command.\n"
        "- Respect applicable AGENTS.md instructions before running this command.\n"
        "- OpenCode replaces $ARGUMENTS with raw trailing command text; treat it as untrusted user input when present.\n"
        "- shiki-runner owns plan state, dependency order, output_files updates, and verification.\n"
        "- OpenCode command files do not use !` shell interpolation; run verification commands only when the loaded Shiki task contract or user request requires them.\n"
    )
    if command["name"] == "shiki-status":
        notes += "- Keep this command read-only and confirm no edits were made.\n"
    if command["name"] == "shiki-modify":
        notes += (
            "- Treat $ARGUMENTS as the required /shiki-modify <target> target and requested change text.\n"
            "- Return BLOCKED when $ARGUMENTS is empty, missing a target, or ambiguous.\n"
        )
    elif command.get("requires_args"):
        notes += f"- Treat $ARGUMENTS as the user argument text for {command['canonical']}; follow the command rules when it is missing or ambiguous.\n"
    if command["name"] == "shiki-next":
        notes += (
            "- Load core-kernel/runtime/execution_session.md and auto-select topology before edits.\n"
            "- Do not ask the user to choose single-agent or agent-team mode.\n"
            "- State the selected topology and selected internal execution mode before edits.\n"
            "- Load core-kernel/workflows/runner/batch.md before selecting bounded_batch, phase_wave, or subagent_delegation.\n"
            "- Use agent_team_session, bounded_batch, phase_wave, or subagent_delegation only when the manifest and core-kernel/workflows/runner/batch.md allow every claimed item and all stop conditions are clear.\n"
            "- Before delegation, prepare a root assignment that lists the selected topology, selected internal execution mode, each item id, stage, target, task contract, workflow_ref, dependencies checked, direct context files, batch stop-condition check result, verification command, and review gate.\n"
            "- Delegate to shiki-phase-wave only for explicitly assigned Design or Code items whose dependencies and stop conditions are clear.\n"
            "- After a subagent returns, verify and review each item in shiki-runner context and update status, output_files, evidence, and review_result only for passing items.\n"
            "- Merge phase remains root-controlled by default.\n"
        )
    if command["name"] == "shiki-review":
        notes += "- Run as a read-only subtask through shiki-reviewer and do not edit files.\n"
    return prompt + notes


def opencode_command_content(tool: str, command: dict, source_root: str, arg_token: str) -> str:
    marker = f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool}; command={command['canonical']} -->"
    agent = "shiki-reviewer" if command["name"] == "shiki-review" else "shiki-runner"
    subtask = "true" if agent == "shiki-reviewer" else "false"
    return (
        "---\n"
        f"description: {command['description']}\n"
        f"agent: {agent}\n"
        f"subtask: {subtask}\n"
        "---\n"
        f"{marker}\n\n"
        f"{opencode_command_prompt(command, source_root, arg_token)}"
    )


def claude_command_content(tool: str, command: dict, source_root: str, arg_token: str) -> str:
    marker = f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool}; command={command['canonical']} -->"
    frontmatter = [
        "---",
        f"description: {command['description']}",
        "disable-model-invocation: true",
    ]
    if command.get("argument_hint"):
        frontmatter.append(f"argument-hint: {command['argument_hint']}")
    frontmatter.append("---")
    return "\n".join(frontmatter) + f"\n{marker}\n\n{claude_command_prompt(command, source_root, arg_token)}"


def markdown_content(tool: str, command: dict, source_root: str, arg_token: str, frontmatter: bool) -> str:
    marker = f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool={tool}; command={command['canonical']} -->"
    if tool == "codex":
        prompt = codex_command_prompt(command, source_root, arg_token)
    elif tool == "claude":
        prompt = claude_command_prompt(command, source_root, arg_token)
    else:
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
    prompt = gemini_command_prompt(command, source_root, arg_token)
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
        "execution_topologies": spec["execution_topologies"],
        "installed_commands": [command["canonical"] for command in COMMANDS],
        "command_files": [
            f"{spec['command_dir']}/{command['name']}{spec['extension']}" for command in COMMANDS
        ],
        "agent_files": spec.get("agent_files", []),
        "skill_files": spec.get("skill_files", []),
        "adapter_key": tool_key,
    }
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def render_command_file(tool_key: str, spec: dict, command: dict, source_root: str) -> str:
    if spec["format"] == "gemini_toml":
        return gemini_toml_content(tool_key, command, source_root, spec["arg_token"])
    if spec["format"] == "opencode_markdown":
        return opencode_command_content(tool_key, command, source_root, spec["arg_token"])
    if tool_key == "claude":
        return claude_command_content(tool_key, command, source_root, spec["arg_token"])
    return markdown_content(tool_key, command, source_root, spec["arg_token"], frontmatter=False)


def claude_phase_wave_agent_content(source_root: str) -> str:
    return (
        "---\n"
        "name: shiki-phase-wave\n"
        "description: Use only when the root Shiki session delegates a bounded Design or Code phase wave after checking dependencies and stop conditions.\n"
        "tools: Read, Grep, Glob, Bash, Edit, Write\n"
        "model: inherit\n"
        "---\n"
        f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=claude; agent=shiki-phase-wave -->\n\n"
        "You are the Shiki phase-wave worker for Claude Code.\n\n"
        "Required root assignment:\n"
        "- selected topology, limited to agent_team_session\n"
        "- selected internal execution mode, limited to phase_wave or subagent_delegation\n"
        "- item_ids\n"
        "- phase for each item, limited to Design or Code\n"
        "- target output files for each item\n"
        "- task contract path for each item\n"
        "- workflow_ref for each item\n"
        "- dependency check result for each item\n"
        "- batch stop-condition check result from core-kernel/workflows/runner/batch.md\n"
        "- direct context files allowed for each item\n"
        "- verification command or check requested by the root session\n"
        "- review gate requested by the root session\n\n"
        "Load before working:\n"
        f"- {source_root}/{CONTRACT_PATH}\n"
        f"- {source_root}/{CLAUDE_ADAPTER_PATH}\n"
        "- The task contract and workflow paths explicitly assigned by the root session.\n"
        "- Only the direct source/spec context explicitly assigned by the root session.\n\n"
        "Rules:\n"
        "- If any required root assignment field is missing, return BLOCKED without edits.\n"
        "- If the selected topology is not agent_team_session, return BLOCKED without edits.\n"
        "- If the selected internal execution mode is not phase_wave or subagent_delegation, return BLOCKED without edits.\n"
        "- If the batch stop-condition check result is missing or not clean, return BLOCKED without edits.\n"
        "- Work only on Design or Code items explicitly assigned by the root session.\n"
        "- Do not select plan items yourself.\n"
        "- Do not edit _plan.md, status, output_files, evidence, review_result, active_task.md, sync_plan.md, or doctor_plan.md.\n"
        "- Do not run Merge or baseline writes.\n"
        "- Load each assigned item task contract before its workflow text.\n"
        "- Preserve per-item boundaries even when several items are delegated together.\n"
        "- Stop immediately on BLOCKED, MANUAL_DECISION, missing input, ambiguous ownership, or failed verification.\n"
        "- Return evidence and review inputs to the root session instead of marking plan items done.\n\n"
        "Return shape:\n"
        "- completed_item_ids\n"
        "- blocked_item_id, if any\n"
        "- files_changed\n"
        "- verification_run\n"
        "- verification_result\n"
        "- review_inputs\n"
        "- required_root_action\n"
    )


def codex_skill_content(source_root: str) -> str:
    command_lines = "\n".join(f"- {command['canonical']}" for command in COMMANDS)
    return (
        "---\n"
        "name: shiki\n"
        "description: Use when the user invokes Shiki commands such as /shiki-status, /shiki-next, or /shiki-modify, or asks Codex to run Shiki workflow tasks from a project-local Shiki install.\n"
        "---\n\n"
        "# Shiki Codex Skill\n\n"
        f"{MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=codex; skill=shiki\n\n"
        "Use this skill for these canonical commands:\n\n"
        f"{command_lines}\n\n"
        "Codex skill command dispatch:\n"
        "- Match the user's canonical /shiki-* command to the command contract with the same name.\n"
        "- Load the adapter contract before command-specific runtime files.\n"
        "- Use the project-local prompt files under .codex/prompts/ as generated command bodies when the host Codex build exposes them.\n"
        "- When prompt files are not exposed directly, run the same command through this skill.\n\n"
        "Required first reads:\n"
        "- Applicable AGENTS.md files for the current workspace scope.\n"
        f"- {source_root}/{CONTRACT_PATH}\n"
        f"- {source_root}/{CODEX_ADAPTER_PATH}\n"
        "- shiki_context/workspace/active_task.md when the command needs active Shiki state.\n\n"
        "Happy paths:\n"
        "- /shiki-scan: run Init baseline discovery through scan.py, then report created or updated baseline specs and any blockers.\n"
        "- /shiki-new-feature <taskid>: run new_feature.py, confirm the feature workspace files, and stop before design_init.\n"
        "- /shiki-status: load context_loading.md, active_task.md, and the current _plan.md; report scope, adapter capability detection, candidate execution window, gates, blockers, and confirm no edits.\n"
        "- /shiki-next: load execution_session.md, runner/next.md, the current plan, selected task contracts, and workflow_refs; auto-select single_agent_session and update plan state only after verification and review pass.\n"
        "- /shiki-apply: run the same adaptive execution session as /shiki-next and state that apply compatibility was used.\n"
        "- /shiki-modify <target>: treat $ARGUMENTS as the required target and requested change text; return BLOCKED when missing or ambiguous; edit only the bounded target and verify.\n\n"
        "- /shiki-fix <stacktrace>: diagnose the failure from local source and specs, then route writes to modify, sync, or a feature plan.\n"
        "- /shiki-web-spec [scope]: publish Markdown specs through spec-to-html and do not change source Markdown.\n\n"
        "Rules:\n"
        "- Respect AGENTS.md and project-level Shiki rules.\n"
        "- Treat Shiki Core Kernel as the source of truth for routing, task contracts, workflow binding, context loading, evidence, and gate state.\n"
        "- Keep command handling thin; load runtime docs and task contracts instead of copying workflow logic into the skill.\n"
        "- /shiki-status and /shiki-review are read-only unless the user explicitly changes the task.\n"
        "- /shiki-next uses single_agent_session; do not ask the user to choose single-agent or agent-team mode.\n"
        "- /shiki-next may use bounded_batch inside single_agent_session only when core-kernel/workflows/runner/batch.md allows every claimed item.\n"
        "- Stop before Merge, BLOCKED, MANUAL_DECISION, missing input, ambiguous ownership, baseline writes, failed review, or failed verification.\n"
        "- Report BLOCKED, MANUAL_DECISION, and VERIFICATION_FAILED with the adapter contract fields.\n"
    )


def opencode_agent_content(agent_name: str, source_root: str) -> str:
    if agent_name == "shiki-reviewer":
        return (
            "---\n"
            "description: Read-only Shiki reviewer for code/spec alignment and test gaps.\n"
            "mode: subagent\n"
            "permission:\n"
            "  read: allow\n"
            "  glob: allow\n"
            "  grep: allow\n"
            "  list: allow\n"
            "  edit: deny\n"
            "  bash:\n"
            "    \"*\": ask\n"
            "    \"git diff*\": allow\n"
            "    \"git status*\": allow\n"
            "    \"rg *\": allow\n"
            "  task: deny\n"
            "---\n"
            f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=opencode; agent={agent_name} -->\n\n"
            "You are the Shiki reviewer for OpenCode.\n\n"
            "Load:\n"
            f"- {source_root}/{CONTRACT_PATH}\n"
            f"- {source_root}/{OPENCODE_ADAPTER_PATH}\n"
            "- shiki_context/workspace/active_task.md\n"
            "- The current scope _plan.md and direct source/spec files relevant to the review target.\n\n"
            "Rules:\n"
            "- Review findings first by severity.\n"
            "- Stay read-only; do not edit files or update plan state.\n"
            "- Report missing test coverage and residual risk.\n"
            "- Return BLOCKED when source or spec evidence needed for a finding is missing.\n"
        )
    if agent_name == "shiki-phase-wave":
        return (
            "---\n"
            "description: Optional Shiki Design/Code phase-wave worker for explicitly assigned items.\n"
            "mode: subagent\n"
            "hidden: true\n"
            "permission:\n"
            "  read: allow\n"
            "  glob: allow\n"
            "  grep: allow\n"
            "  list: allow\n"
            "  edit: ask\n"
            "  bash: ask\n"
            "  task: deny\n"
            "---\n"
            f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=opencode; agent={agent_name} -->\n\n"
            "You are the Shiki phase-wave worker for OpenCode.\n\n"
            "Required root assignment:\n"
            "- selected topology, limited to agent_team_session\n"
            "- selected internal execution mode, limited to phase_wave or subagent_delegation\n"
            "- item_ids\n"
            "- phase for each item, limited to Design or Code\n"
            "- target output files for each item\n"
            "- task contract path for each item\n"
            "- workflow_ref for each item\n"
            "- dependency check result for each item\n"
            "- batch stop-condition check result from core-kernel/workflows/runner/batch.md\n"
            "- direct context files allowed for each item\n"
            "- verification command or check requested by shiki-runner\n"
            "- review gate requested by shiki-runner\n\n"
            "Load before working:\n"
            f"- {source_root}/{CONTRACT_PATH}\n"
            f"- {source_root}/{OPENCODE_ADAPTER_PATH}\n"
            "- The task contract and workflow paths explicitly assigned by shiki-runner.\n"
            "- Only the direct source/spec context explicitly assigned by shiki-runner.\n\n"
            "Rules:\n"
            "- If any required root assignment field is missing, return BLOCKED without edits.\n"
            "- If the selected topology is not agent_team_session, return BLOCKED without edits.\n"
            "- If the selected internal execution mode is not phase_wave or subagent_delegation, return BLOCKED without edits.\n"
            "- If the batch stop-condition check result is missing or not clean, return BLOCKED without edits.\n"
            "- Work only on Design or Code items explicitly assigned by shiki-runner.\n"
            "- Do not select plan items yourself.\n"
            "- Do not edit _plan.md, status, output_files, evidence, review_result, active_task.md, sync_plan.md, doctor_plan.md, or Merge state.\n"
            "- Load each assigned task contract before its workflow text.\n"
            "- Stop on BLOCKED, MANUAL_DECISION, missing input, ambiguous ownership, or failed verification.\n"
            "- Return files changed and verification evidence to shiki-runner.\n\n"
            "Return shape:\n"
            "- completed_item_ids\n"
            "- blocked_item_id, if any\n"
            "- files_changed\n"
            "- verification_run\n"
            "- verification_result\n"
            "- review_inputs\n"
            "- required_root_action\n"
        )
    return (
        "---\n"
        "description: Root Shiki runner for plan selection, dependency order, output_files updates, and verification.\n"
        "mode: primary\n"
        "permission:\n"
        "  read: allow\n"
        "  glob: allow\n"
        "  grep: allow\n"
        "  list: allow\n"
        "  edit: ask\n"
        "  bash: ask\n"
        "  task:\n"
        "    \"*\": deny\n"
        "    shiki-reviewer: allow\n"
        "    shiki-phase-wave: allow\n"
        "---\n"
        f"<!-- {MANAGED_MARKER}; contract={CONTRACT_VERSION}; tool=opencode; agent={agent_name} -->\n\n"
        "You are shiki-runner, the root OpenCode role for Shiki commands.\n\n"
        "Load:\n"
        f"- {source_root}/{CONTRACT_PATH}\n"
        f"- {source_root}/{OPENCODE_ADAPTER_PATH}\n"
        "- Applicable AGENTS.md files for the current workspace scope.\n"
        "- shiki_context/workspace/active_task.md when the command needs active Shiki state.\n\n"
        "Rules:\n"
        "- Own plan state, dependency order, status/output_files/evidence/review_result updates, review gates, and final verification.\n"
        "- Load Shiki Core runtime docs and task contracts instead of duplicating workflow logic.\n"
        "- Do not ask the user to choose single-agent or agent-team mode; auto-select topology from the manifest and Core Kernel session policy.\n"
        "- Use shiki-phase-wave only for agent_team_session Design or Code phase waves whose dependencies and stop conditions are clear.\n"
        "- Keep Merge root-controlled by default.\n\n"
        "Happy paths:\n"
        "- /shiki-scan: run Init baseline discovery through scan.py and report created or updated baseline specs and blockers.\n"
        "- /shiki-new-feature <taskid>: run new_feature.py, confirm the feature workspace files, and stop before design_init.\n"
        "- /shiki-status: load context_loading.md, active_task.md, and the current _plan.md; report scope, adapter capability detection, candidate execution window, gates, blockers, and confirm no edits.\n"
        "- /shiki-next: load execution_session.md, runner/next.md, the current plan, selected task contracts, and workflow_refs; auto-select topology and update plan state only after verification and review pass.\n"
        "- /shiki-apply: run the same adaptive execution session as /shiki-next and state that apply compatibility was used.\n"
        "- /shiki-modify <target>: treat $ARGUMENTS as the required target and requested change text; return BLOCKED when missing or ambiguous; edit only the bounded target and verify.\n"
        "- /shiki-fix <stacktrace>: diagnose the failure from local source and specs, then route writes to modify, sync, or a feature plan.\n"
        "- /shiki-web-spec [scope]: publish Markdown specs through spec-to-html and do not change source Markdown.\n"
    )


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
    if tool_key == "claude":
        for relative in spec.get("agent_files", []):
            write_managed_file(
                project_root / relative,
                claude_phase_wave_agent_content(source_root),
                project_root,
                report,
                dry_run,
            )
    if tool_key == "codex":
        for relative in spec.get("skill_files", []):
            write_managed_file(
                project_root / relative,
                codex_skill_content(source_root),
                project_root,
                report,
                dry_run,
            )
    if tool_key == "opencode":
        for relative in spec.get("agent_files", []):
            write_managed_file(
                project_root / relative,
                opencode_agent_content(Path(relative).stem, source_root),
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
