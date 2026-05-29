#!/usr/bin/env python3
"""
Local verification entrypoint for Shiki framework changes.

This script creates a temporary sample project, injects a deterministic devagent
shim, and verifies the filesystem-level workflow.
"""

import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core-kernel"))
CORE_COPY_DIRS = ["docs", "core-kernel", "tools-skills", "tech-stacks", "providers", "user-interface"]
EXPECTED_CONTEXT_DIRS = [
    "shiki_context/workspace",
    "shiki_context/constitution",
    "shiki_context/project",
    "shiki_context/modules",
    "shiki_context/features",
]
EXPECTED_CONTEXT_FILES = [
    "shiki_context/project/README.md",
    "shiki_context/project/index.md",
    "shiki_context/project/_plan.md",
    "shiki_context/project/architecture.md",
    "shiki_context/project/ubiquitous_language.md",
    "shiki_context/project/techstack.md",
    "shiki_context/project/integration.md",
    "shiki_context/workspace/.gitignore",
    "shiki_context/workspace/active_task.md",
    "shiki_context/workspace/_plan.md",
    "shiki_context/constitution/tech_contracts/README.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/acl.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/exception.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/layering.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/naming.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/persistence.md",
]
EXPECTED_ADAPTER_FILES = [
    ".shiki/adapters/codex/manifest.json",
    ".shiki/adapters/claude/manifest.json",
    ".shiki/adapters/gemini/manifest.json",
    ".shiki/adapters/opencode/manifest.json",
    ".codex/prompts/shiki-init.md",
    ".codex/prompts/shiki-status.md",
    ".codex/prompts/shiki-next.md",
    ".codex/prompts/shiki-modify.md",
    ".codex/prompts/shiki-review.md",
    ".codex/prompts/shiki-sync.md",
    ".codex/prompts/shiki-doctor.md",
    ".codex/skills/shiki/SKILL.md",
    ".claude/commands/shiki-init.md",
    ".claude/commands/shiki-status.md",
    ".claude/commands/shiki-next.md",
    ".claude/commands/shiki-modify.md",
    ".claude/commands/shiki-review.md",
    ".claude/commands/shiki-sync.md",
    ".claude/commands/shiki-doctor.md",
    ".claude/agents/shiki-phase-wave.md",
    ".gemini/commands/shiki-init.toml",
    ".gemini/commands/shiki-status.toml",
    ".gemini/commands/shiki-next.toml",
    ".gemini/commands/shiki-modify.toml",
    ".gemini/commands/shiki-review.toml",
    ".gemini/commands/shiki-sync.toml",
    ".gemini/commands/shiki-doctor.toml",
    ".opencode/commands/shiki-init.md",
    ".opencode/commands/shiki-status.md",
    ".opencode/commands/shiki-next.md",
    ".opencode/commands/shiki-modify.md",
    ".opencode/commands/shiki-review.md",
    ".opencode/commands/shiki-sync.md",
    ".opencode/commands/shiki-doctor.md",
    ".opencode/agents/shiki-runner.md",
    ".opencode/agents/shiki-reviewer.md",
    ".opencode/agents/shiki-phase-wave.md",
]
TEXT_SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    "__pycache__",
    "tmp",
}
TEXT_SKIP_FILES = set()
TEXT_SKIP_SUFFIXES = {".zip", ".pyc"}
DISALLOWED_TEXT = [
    "batch_analysis.py",
    "Context Engineering System",
    "design_plan.md",
    "design_status.md",
    "2_module",
    "designs/*_contract.md",
    "order_contract.md",
]
PHASE_RE = re.compile(r"^## (Phase \d+: [^\n]+)(.*?)(?=^## Phase |\Z)", re.S | re.M)


def log(message: str) -> None:
    print(f"[verify] {message}")


def run(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    log("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def run_expect_fail(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    log("$ " + " ".join(cmd) + "  # expected failure")
    result = subprocess.run(cmd, cwd=str(cwd), env=env)
    if result.returncode == 0:
        raise AssertionError("Expected command to fail: " + " ".join(cmd))


def require_file(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Expected file missing: {path}")


def require_dir(path: Path) -> None:
    if not path.is_dir():
        raise AssertionError(f"Expected directory missing: {path}")


def require_workspace_ignore_policy(path: Path) -> None:
    require_file(path)
    content = path.read_text(encoding="utf-8")
    for needle in [
        "/*",
        "!/.gitignore",
        "Ignore everything created under this workspace directory.",
    ]:
        if needle not in content:
            raise AssertionError(f"{path} missing workspace ignore rule: {needle}")


def python_scripts() -> list[str]:
    files = []
    for base in [ROOT / "core-kernel" / "_lib", ROOT / "tools-skills" / "scripts"]:
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(str(path.relative_to(ROOT)))
    return files


def verify_python_and_shell() -> None:
    log("checking Python scripts")
    run([sys.executable, "-m", "py_compile", *python_scripts()])


def should_scan_text(path: Path) -> bool:
    if any(part in TEXT_SKIP_DIRS for part in path.parts):
        return False
    if path.name in TEXT_SKIP_FILES:
        return False
    if path.suffix in TEXT_SKIP_SUFFIXES:
        return False
    if path == ROOT / "tools-skills" / "scripts" / "verify.py":
        return False
    if path == ROOT / "tools-skills" / "scripts" / "simulate_scenarios.py":
        return False
    return path.is_file()


def verify_static_text() -> None:
    log("checking stale references")
    failures = []
    for path in ROOT.rglob("*"):
        if not should_scan_text(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for needle in DISALLOWED_TEXT:
            if needle in content:
                failures.append(f"{path.relative_to(ROOT)} contains {needle!r}")
    if failures:
        raise AssertionError("\n".join(failures))


def verify_core_consistency() -> None:
    log("checking core file consistency")
    cheatsheet = (ROOT / "docs" / "CHEATSHEET.md").read_text(encoding="utf-8")
    phase_contract = (ROOT / "core-kernel/runtime/phase_contract.md").read_text(encoding="utf-8")
    context_loading = (ROOT / "core-kernel/runtime/context_loading.md").read_text(encoding="utf-8")
    adapter_contract = (ROOT / "user-interface" / "adapters" / "tool_adapter_contract_v1.md").read_text(encoding="utf-8")
    codex_adapter = (ROOT / "user-interface" / "adapters" / "codex_adapter.md").read_text(encoding="utf-8")
    claude_adapter = (ROOT / "user-interface" / "adapters" / "claude_code_adapter.md").read_text(encoding="utf-8")
    gemini_adapter = (ROOT / "user-interface" / "adapters" / "gemini_cli_adapter.md").read_text(encoding="utf-8")
    opencode_adapter = (ROOT / "user-interface" / "adapters" / "opencode_adapter.md").read_text(encoding="utf-8")
    runner_next = (ROOT / "core-kernel" / "workflows" / "runner" / "next.md").read_text(encoding="utf-8")
    runner_apply = (ROOT / "core-kernel" / "workflows" / "runner" / "apply.md").read_text(encoding="utf-8")
    runner_batch = (ROOT / "core-kernel" / "workflows" / "runner" / "batch.md").read_text(encoding="utf-8")
    feature_plan_template = (ROOT / "core-kernel" / "templates" / "feature" / "_plan.md").read_text(encoding="utf-8")
    require_workspace_ignore_policy(ROOT / "core-kernel" / "templates" / "workspace" / ".gitignore")

    # Check CHEATSHEET has the active prompt entries
    for heading in [
        "## 1. scan",
        "## 2. new feature",
        "## 3. status",
        "## 4. next",
        "## 4a. apply",
        "## 4b. batch",
        "## 5. review",
        "## 6. modify",
        "## 7. doctor",
        "## 8. sync",
    ]:
        if heading not in cheatsheet:
            raise AssertionError(f"CHEATSHEET.md missing entry: {heading}")

    # No legacy headings
    for stale in ["verify last", "status check", "run next"]:
        if stale in cheatsheet:
            raise AssertionError(f"CHEATSHEET.md still contains legacy heading: {stale}")

    # Check phase enum matches active_task template
    active_task = (ROOT / "core-kernel" / "templates" / "workspace" / "active_task.md").read_text(encoding="utf-8")
    contract_enum_match = re.search(r"Use this enum for the `stage` field in `active_task\.md`:\n\n```(?:text)?\n([^`]+)\n```", phase_contract)
    active_enum_match = re.search(r"`stage`: \[([^\]]+)\]", active_task)
    if contract_enum_match and active_enum_match:
        contract_enum = contract_enum_match.group(1).replace(" ", "").strip()
        active_enum = active_enum_match.group(1).replace("/", "|").replace(" ", "").strip()
        if contract_enum != active_enum:
            raise AssertionError(f"Phase enum mismatch: contract={contract_enum!r}, active_task={active_enum!r}")

    # Check all task contract YAMLs have required fields
    for contract_path in sorted((ROOT / "core-kernel" / "runtime" / "task_contracts").rglob("*.yaml")):
        from _lib.task_contracts import _load_yaml
        data = _load_yaml(contract_path.read_text(encoding="utf-8"))
        required = ["id", "stage", "goal", "output", "workflow_ref"]
        legacy_output_key = "arti" + "fact"
        if legacy_output_key in data:
            raise AssertionError(f"{contract_path.relative_to(ROOT)} uses legacy output field")
        if "kind" in data:
            raise AssertionError(f"{contract_path.relative_to(ROOT)} uses legacy kind field")
        missing = [field for field in required if field not in data]
        if missing:
            raise AssertionError(f"{contract_path.relative_to(ROOT)} missing fields: {', '.join(missing)}")

    # Check all workflow_ref resolve
    for contract_path in sorted((ROOT / "core-kernel" / "runtime" / "task_contracts").rglob("*.yaml")):
        from _lib.task_contracts import _load_yaml
        data = _load_yaml(contract_path.read_text(encoding="utf-8"))
        ref = data.get("workflow_ref", "")
        if ref and not (ROOT / ref).exists():
            raise AssertionError(f"{contract_path.relative_to(ROOT)}: workflow_ref '{ref}' does not exist")

    # Check no S-numbering in active paths
    for d in [ROOT / "core-kernel" / "workflows", ROOT / "core-kernel" / "runtime" / "task_contracts"]:
        for f in d.rglob("*"):
            if f.is_file() and re.match(r"s[0-9]", f.name):
                raise AssertionError(f"S-numbered file in active path: {f.relative_to(ROOT)}")

    # Check runtime guidance
    for needle in ["task contract", "core-kernel/runtime/task_contracts/"]:
        if needle not in context_loading + runner_next + runner_apply + runner_batch:
            raise AssertionError(f"Missing task-contract runtime guidance: {needle}")
    for needle in ["feature-root relative", "not baseline"]:
        if needle not in context_loading + runner_next + feature_plan_template:
            raise AssertionError(f"Missing feature-relative target guidance: {needle}")
    if "top-level prompt" not in context_loading:
        raise AssertionError("Missing user-facing top-level prompt guidance")

    # Check the tool-native adapter contract covers the Phase 1 command surface
    for needle in [
        "Contract Version: v1",
        "Shiki Core remains the source of truth",
        "supports_slash_commands",
        "supports_skills",
        "supports_subagents",
        "supports_project_local_install",
        "single_item",
        "bounded_batch",
        "phase_wave",
        "subagent_delegation",
        "Installed Adapter File Expectations",
        "Regression checks must verify installed adapter files",
        "BLOCKED",
        "MANUAL_DECISION",
        "VERIFICATION_FAILED",
        "Codex",
        "Claude Code",
        "Gemini CLI",
        "OpenCode",
    ]:
        if needle not in adapter_contract:
            raise AssertionError(f"adapter contract missing expected guidance: {needle}")
    for command in [
        "/shiki-init",
        "/shiki-status",
        "/shiki-next",
        "/shiki-modify <target>",
        "/shiki-review",
        "/shiki-sync",
        "/shiki-doctor",
    ]:
        if command not in adapter_contract:
            raise AssertionError(f"adapter contract missing command: {command}")
    for core_ref in [
        "core-kernel/runtime/context_loading.md",
        "core-kernel/workflows/runner/next.md",
        "core-kernel/workflows/runner/batch.md",
        "core-kernel/runtime/task_contracts/sync/plan.yaml",
        "core-kernel/runtime/task_contracts/sync/apply_leaf.yaml",
        "core-kernel/runtime/task_contracts/doctor/plan.yaml",
        "core-kernel/runtime/task_contracts/doctor/apply_item.yaml",
    ]:
        if core_ref not in adapter_contract:
            raise AssertionError(f"adapter contract missing Core Kernel reference: {core_ref}")
    for needle in [
        ".codex/prompts/shiki-status.md",
        ".codex/skills/shiki/SKILL.md",
        "AGENTS.md",
        "`single_item` mode by default",
        "switch `/shiki-next` to `bounded_batch`",
        "Verification covers installed Codex adapter files",
    ]:
        if needle not in codex_adapter:
            raise AssertionError(f"Codex adapter doc missing expected guidance: {needle}")
    for needle in [
        ".gemini/commands/shiki-status.toml",
        "/shiki-modify <target>",
        "{{args}}",
        "core-kernel/runtime/context_loading.md",
        "`bounded_batch`",
        "project-local `.gemini/commands/*.toml`",
    ]:
        if needle not in gemini_adapter:
            raise AssertionError(f"Gemini adapter doc missing expected guidance: {needle}")
    for needle in [
        ".opencode/commands/shiki-status.md",
        ".opencode/agents/",
        "shiki-runner",
        "shiki-reviewer",
        "shiki-phase-wave",
        "plan state and verification",
        "Merge remains",
    ]:
        if needle not in opencode_adapter:
            raise AssertionError(f"OpenCode adapter doc missing expected guidance: {needle}")
    for needle in [
        ".claude/commands/",
        ".claude/agents/shiki-phase-wave.md",
        "Design or Code phase wave",
        "Merge phase remains root-controlled",
        "The `shiki-phase-wave` subagent must not select its own plan items",
        "context limits",
        "unsafe",
    ]:
        if needle not in claude_adapter:
            raise AssertionError(f"Claude adapter doc missing expected guidance: {needle}")

    # Feature overlay specs must carry explicit baseline delta metadata for merge.
    delta_types = ["reuse", "add", "extend", "modify", "deprecate"]
    delta_templates = [
        ROOT / "core-kernel" / "templates" / "module" / "designs" / "_model_template.md",
        ROOT / "core-kernel" / "templates" / "module" / "designs" / "_persistence_template.md",
        ROOT / "core-kernel" / "templates" / "module" / "designs" / "_acl_template.md",
        ROOT / "core-kernel" / "templates" / "module" / "designs" / "_component_template.md",
        ROOT / "core-kernel" / "templates" / "module" / "entrances" / "_entrance_spec_template.md",
        ROOT / "core-kernel" / "templates" / "module" / "flows" / "_flow_template.md",
    ]
    for template_path in delta_templates:
        content = template_path.read_text(encoding="utf-8")
        for needle in ["Baseline Delta", "change_type", "baseline_ref", "overlay_ref", "merge_action", *delta_types]:
            if needle not in content:
                raise AssertionError(f"{template_path.relative_to(ROOT)} missing baseline delta marker: {needle}")

    delta_workflows = [
        ROOT / "core-kernel" / "workflows" / "design" / "model.md",
        ROOT / "core-kernel" / "workflows" / "design" / "persistence.md",
        ROOT / "core-kernel" / "workflows" / "design" / "acl.md",
        ROOT / "core-kernel" / "workflows" / "design" / "component.md",
        ROOT / "core-kernel" / "workflows" / "design" / "entrance_spec.md",
        ROOT / "core-kernel" / "workflows" / "design" / "flow.md",
    ]
    for workflow_path in delta_workflows:
        content = workflow_path.read_text(encoding="utf-8")
        for needle in ["Baseline Delta", *delta_types, "MANUAL_DECISION"]:
            if needle not in content:
                raise AssertionError(f"{workflow_path.relative_to(ROOT)} missing baseline delta guidance: {needle}")
    merge_workflow = (ROOT / "core-kernel" / "workflows" / "merge" / "feature_merge.md").read_text(encoding="utf-8")
    for needle in ["Baseline Delta", "change_type", *delta_types]:
        if needle not in merge_workflow:
            raise AssertionError(f"feature_merge.md missing baseline delta merge rule: {needle}")


def copy_shiki_to(project: Path) -> None:
    shiki_dir = project / "shiki"
    shiki_dir.mkdir()
    for name in CORE_COPY_DIRS:
        src = ROOT / name
        if src.exists():
            shutil.copytree(src, shiki_dir / name)
    for name in [
        "shiki.config.yaml",
        "README.md",
    ]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, shiki_dir / name)


def write_devagent_shim(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    shim = bin_dir / "devagent"
    shim.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import re
            import sys
            from pathlib import Path

            prompt = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else ""
            ctx = Path("shiki_context")

            def write(path, content):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            if "Scan Dependencies" in prompt:
                write(ctx / "project" / "techstack.md", "# Tech Stack\\n\\n## Stack Choices\\n\\n- Spring Boot\\n")
                write(ctx / "project" / "integration.md", "# Integration\\n\\n## Data Sources\\n\\nN/A\\n")
                sys.exit(0)

            if "Entrance Analysis" in prompt:
                match = re.search(r"Module: (\\w+)", prompt)
                module = match.group(1) if match else "order"
                write(ctx / "modules" / module / "entrances" / "create_order.md", "# Entrance Spec: create_order\\n")
                write(ctx / "modules" / module / "flows" / "create_order.md", "# Flow: create_order\\n")
                sys.exit(0)

            if "Discovery Sync" in prompt:
                write(ctx / "project" / "tech_debt.md", "# Tech Debt\\n\\nN/A\\n")
                write(ctx / "project" / "integration.md", "# Integration\\n\\n## Data Sources\\n\\nN/A\\n")
                sys.exit(0)

            sys.exit(0)
            """
        ),
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)


def verify_fixture_workflow() -> None:
    log("checking fixture workflow with devagent shim")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        project = tmp / "project"
        shutil.copytree(ROOT / "tests" / "fixtures" / "java-ddd-spring-sample", project)
        copy_shiki_to(project)

        shim_bin = tmp / "bin"
        write_devagent_shim(shim_bin)
        env = os.environ.copy()
        env["PATH"] = f"{shim_bin}{os.pathsep}{env.get('PATH', '')}"

        run([sys.executable, "shiki/tools-skills/scripts/init.py"], cwd=project, env=env)
        for relative in EXPECTED_CONTEXT_DIRS:
            require_dir(project / relative)
        for relative in EXPECTED_CONTEXT_FILES:
            require_file(project / relative)
        require_workspace_ignore_policy(project / "shiki_context" / "workspace" / ".gitignore")
        if (project / "shiki_context" / "module").exists():
            raise AssertionError("init.py must not create legacy shiki_context/module/")

        # Init idempotency
        run([sys.executable, "shiki/tools-skills/scripts/init.py"], cwd=project, env=env)

        adapter_dry_plan = subprocess.check_output(
            [sys.executable, "shiki/tools-skills/scripts/install_agent_adapter.py", "--tool", "all", "--dry-run"],
            cwd=str(project),
            env=env,
            text=True,
        )
        if "Would create" not in adapter_dry_plan or "Result: plan only" not in adapter_dry_plan:
            raise AssertionError("adapter installer dry-run must print a write plan")
        if (project / ".claude" / "commands" / "shiki-status.md").exists():
            raise AssertionError("adapter installer dry-run must not write command files")

        adapter_install = subprocess.check_output(
            [sys.executable, "shiki/tools-skills/scripts/install_agent_adapter.py", "--tool", "all"],
            cwd=str(project),
            env=env,
            text=True,
        )
        if "Created" not in adapter_install or "Blocked (0 files)" not in adapter_install:
            raise AssertionError("adapter installer must report created and blocked file counts")
        adapter_repeat = subprocess.check_output(
            [sys.executable, "shiki/tools-skills/scripts/install_agent_adapter.py", "--tool", "all"],
            cwd=str(project),
            env=env,
            text=True,
        )
        if "Skipped" not in adapter_repeat or "Result: adapter files installed" not in adapter_repeat:
            raise AssertionError("adapter installer must be idempotent")
        for relative in EXPECTED_ADAPTER_FILES:
            require_file(project / relative)
        adapter_text = "\n".join((project / relative).read_text(encoding="utf-8") for relative in EXPECTED_ADAPTER_FILES)
        for needle in [
            "adapter_contract_version",
            "v1",
            "/shiki-status",
            "/shiki-next",
            "/shiki-modify <target>",
            "shiki-phase-wave",
            "Merge phase remains root-controlled",
            "AGENTS.md",
            "bounded_batch",
            ".codex/skills/shiki/SKILL.md",
            ".gemini/commands/shiki-status.toml",
            "{{args}}",
            ".opencode/commands/shiki-status.md",
            ".opencode/agents/shiki-runner.md",
            "shiki-reviewer",
            "core-kernel/runtime/context_loading.md",
            "core-kernel/runtime/task_contracts/",
            "Shiki Adapter: managed",
        ]:
            if needle not in adapter_text:
                raise AssertionError(f"installed adapter files missing expected content: {needle}")

        outside_root = tmp / "outside-project"
        outside_root.mkdir()
        outside_result = subprocess.run(
            [
                sys.executable,
                "shiki/tools-skills/scripts/install_agent_adapter.py",
                "--tool",
                "codex",
                "--project-root",
                str(outside_root),
            ],
            cwd=str(project),
            env=env,
            text=True,
            capture_output=True,
        )
        if outside_result.returncode == 0 or "refusing to write outside the current project" not in outside_result.stderr:
            raise AssertionError("adapter installer must refuse unsafe outside-project writes")

        user_owned_command = project / ".claude" / "commands" / "shiki-status.md"
        user_owned_command.write_text("user-owned command\n", encoding="utf-8")
        blocked_result = subprocess.run(
            [sys.executable, "shiki/tools-skills/scripts/install_agent_adapter.py", "--tool", "claude"],
            cwd=str(project),
            env=env,
            text=True,
            capture_output=True,
        )
        if blocked_result.returncode == 0 or "Blocked" not in blocked_result.stdout:
            raise AssertionError("adapter installer must block existing non-managed command files")

        run([sys.executable, "shiki/tools-skills/scripts/scan.py", "--only", "s0.1"], cwd=project, env=env)
        run([sys.executable, "shiki/tools-skills/scripts/scan.py", "--only", "s0.2"], cwd=project, env=env)
        run([sys.executable, "shiki/tools-skills/scripts/batch_analyze.py"], cwd=project, env=env)
        for relative in [
            "shiki_context/modules/order/entrances/create_order.md",
            "shiki_context/modules/order/flows/create_order.md",
            "shiki_context/modules/order/README.md",
            "shiki_context/modules/order/index.md",
            "shiki_context/modules/order/_plan.md",
            "shiki_context/project/tech_debt.md",
        ]:
            require_file(project / relative)
        init_plan = (project / "shiki_context" / "workspace" / "_plan.md").read_text(encoding="utf-8")
        if "init.entrance" not in init_plan or "entrances/create_order.md" not in init_plan:
            raise AssertionError("scan.py must analyze entries, not only register them")
        project_index = (project / "shiki_context" / "project" / "index.md").read_text(encoding="utf-8")
        if "| `order` | `modules/order/` | `modules/order/index.md` | current |" not in project_index:
            raise AssertionError("scan.py must register discovered modules in project index.md")
        if (project / "shiki_context" / "module").exists():
            raise AssertionError("scan.py must not use legacy shiki_context/module/ as active baseline")

        # new_feature creates feature scope trio plus bootstrap lifecycle files
        run([sys.executable, "shiki/tools-skills/scripts/new_feature.py", "--taskid", "FEAT-VERIFY"], cwd=project, env=env)
        feature_dir = project / "shiki_context" / "features" / "FEAT-VERIFY"
        require_file(feature_dir / "design_brief.md")
        feature_template_root = ROOT / "core-kernel" / "templates" / "feature"
        for template_path in sorted(feature_template_root.rglob("*")):
            if template_path.is_file():
                if template_path.relative_to(feature_template_root).as_posix() == "code_contract.md":
                    continue
                require_file(feature_dir / template_path.relative_to(feature_template_root))

        # Verify NO legacy files created
        for should_not_exist in ["review_spec.md", "implementation_plan.md", "verification_report.md"]:
            if (feature_dir / should_not_exist).exists():
                raise AssertionError(f"new_feature.py should not create {should_not_exist}")
        if (feature_dir / "draft_specs").exists():
            raise AssertionError("new_feature.py should not create draft_specs/")
        if (feature_dir / "change_requests").exists():
            raise AssertionError("new_feature.py should not create change_requests/")
        if (feature_dir / "evidence").exists():
            raise AssertionError("new_feature.py should not create evidence/")

        brief_path = feature_dir / "design_brief.md"
        brief_text = brief_path.read_text(encoding="utf-8")
        brief_path.write_text(
            brief_text.replace(
                "**Module**: [optional; design_init may infer it]",
                "**Module**: order",
            ),
            encoding="utf-8",
        )

        plan_text = (feature_dir / "_plan.md").read_text(encoding="utf-8")
        if "| B1 | Design | `_plan.md` | - | `core-kernel/runtime/task_contracts/design/design_init.yaml` |" not in plan_text:
            raise AssertionError("new_feature.py must create a bootstrap plan with design_init")

        # Kernel routing: bootstrap should drive design_init
        select_bootstrap = subprocess.check_output(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'shiki/core-kernel'); "
                    "from pathlib import Path; "
                    "from _lib.kernel import select_next_item; "
                    "item, contract = select_next_item(Path('shiki_context/features/FEAT-VERIFY')); "
                    "print(item['id']); "
                    "print(contract['id'])"
                ),
            ],
            cwd=str(project),
            env=env,
            text=True,
        ).strip().splitlines()
        if select_bootstrap != ["B1", "design_init"]:
            raise AssertionError(f"bootstrap plan did not drive design_init: {select_bootstrap!r}")

        # Expand plan
        subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'shiki/core-kernel'); "
                    "from pathlib import Path; "
                    "from _lib.feature_plan import expand_plan_from_brief; "
                    "expand_plan_from_brief(Path('shiki_context/features/FEAT-VERIFY'), 'FEAT-VERIFY')"
                ),
            ],
            cwd=str(project),
            env=env,
            check=True,
        )
        plan_text = (feature_dir / "_plan.md").read_text(encoding="utf-8")
        for needle in [
            "| D1 | Design | `modules/order/designs/model.md` | - | `core-kernel/runtime/task_contracts/design/model.yaml` |",
            "| C1 | Code | - | D1,D6 | `core-kernel/runtime/task_contracts/code/entity.yaml` |",
            "| M1 | Merge | baseline | C5 | `core-kernel/runtime/task_contracts/merge/feature_merge.yaml` |",
        ]:
            if needle not in plan_text:
                raise AssertionError(f"expanded plan missing row: {needle}")
        feature_index_text = (feature_dir / "index.md").read_text(encoding="utf-8")
        if "| `modules.order.designs.model` | `modules/order/designs/model.md` | D1 |" not in feature_index_text:
            raise AssertionError("design_init expansion must update feature index.md")
        if "Baseline Delta" not in feature_index_text or "reuse/add/extend/modify/deprecate" not in feature_index_text:
            raise AssertionError("feature index.md must preserve baseline delta guidance")

        batch_select = subprocess.check_output(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'shiki/core-kernel'); "
                    "from pathlib import Path; "
                    "from _lib.kernel import route_batch_items; "
                    "routes = route_batch_items(Path('shiki_context/features/FEAT-VERIFY'), max_items=2); "
                    "print(','.join(route.item['id'] for route in routes)); "
                    "print(','.join(route.contract['id'] for route in routes))"
                ),
            ],
            cwd=str(project),
            env=env,
            text=True,
        ).strip().splitlines()
        if batch_select != ["D1,D2", "model,persistence"]:
            raise AssertionError(f"batch routing did not preserve ordered task atoms: {batch_select!r}")


def verify_publish_docs() -> None:
    log("checking Markdown HTML publisher")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        docs = tmp / "docs"
        site_root = tmp / "site"
        site = site_root / "web_spec"
        docs.mkdir()
        (docs / "README.md").write_text(
            textwrap.dedent(
                """\
                # Docs Home

                See [Guide](guide.md).

                | Name | Value |
                | :--- | :--- |
                | Runtime | `Shiki` |

                ```mermaid
                flowchart LR
                    A[Spec] --> B[HTML]
                ```
                """
            ),
            encoding="utf-8",
        )
        (docs / "guide.md").write_text("# Guide\n\nBack to [Home](README.md).\n", encoding="utf-8")

        run(
            [
                sys.executable,
                "tools-skills/scripts/publish_docs.py",
                str(docs),
                "--output",
                str(site_root),
                "--title",
                "Test Docs",
                "--fail-on-broken-links",
            ]
        )
        require_file(site / "index.html")
        require_file(site / "README.html")
        require_file(site / "guide.html")
        require_file(site / "publish_report.md")
        require_file(site / "assets" / "site.css")
        require_file(site / "assets" / "site.js")
        require_file(site / "assets" / "highlight.min.js")
        require_file(site / "assets" / "highlight-theme.css")
        require_file(site / "assets" / "mermaid.min.js")

        readme_html = (site / "README.html").read_text(encoding="utf-8")
        guide_html = (site / "guide.html").read_text(encoding="utf-8")
        site_js = (site / "assets" / "site.js").read_text(encoding="utf-8")
        report = (site / "publish_report.md").read_text(encoding="utf-8")
        for needle in [
            'href="guide.html"',
            "<table>",
            'class="diagram"',
            'data-diagram-action="open"',
            "diagram-viewer-stage",
            "normalizeMermaidSvg",
            "dataset.diagramWidth",
            '"inline"',
            'svg.style.maxWidth = width + "px"',
            'class="view-controls"',
            'data-layout-action="focus"',
            "specToHtmlLayout",
            "focus-mode",
            'class="nav-tree"',
            'class="toc-panel"',
            'class="toc-item toc-level-1"',
            "code-copy",
            "assets/highlight.min.js",
            "assets/mermaid.min.js",
            "Broken Markdown Links",
            "- None",
        ]:
            if needle not in readme_html + report + site_js:
                raise AssertionError(f"published docs missing expected content: {needle}")
        if 'href="README.html"' not in guide_html:
            raise AssertionError("publisher must rewrite local .md links to .html links")


def verify_pretty_shiki_spec() -> None:
    log("checking Pretty Shiki spec publisher")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        project = tmp / "project"
        ctx = project / "shiki_context"
        feature = ctx / "features" / "FEAT-PRETTY"
        module_designs = feature / "modules" / "order" / "designs"
        tests_dir = feature / "tests"
        baseline_module = ctx / "modules" / "order"
        for path in [
            ctx / "project",
            ctx / "workspace",
            module_designs,
            tests_dir,
            baseline_module,
        ]:
            path.mkdir(parents=True, exist_ok=True)
        (ctx / "project" / "index.md").write_text("# Project Index\n", encoding="utf-8")
        (ctx / "project" / "architecture.md").write_text(
            "# Architecture\n\n## Overview\n\nOrder service baseline.\n",
            encoding="utf-8",
        )
        (ctx / "workspace" / "active_task.md").write_text("# Active Task\n", encoding="utf-8")
        (baseline_module / "index.md").write_text(
            textwrap.dedent(
                """\
                # Module Index: order

                ## Business Boundary

                - **Core Responsibility**: order lifecycle
                - **Domain Entities**: Order
                - **Out of Scope**: payment
                """
            ),
            encoding="utf-8",
        )
        (feature / "design_brief.md").write_text(
            textwrap.dedent(
                """\
                # Design Brief: Pretty Spec

                **Module**: order  **Date**: 2026-05-25  **Author**: tester
                **Source**: verification

                ## 1. Summary

                Create a readable spec for order review.

                ## 2. Core Concepts

                - Order

                ## 3. State Changes

                - Order: INIT -> REVIEWED

                ## 4. Operations

                - Review order

                ## 5. Business Rules

                - Only submitted orders can be reviewed.

                ## 6. External Entrances and Capacity

                - N/A - no exposed entry changes.

                ## 7. Boundaries and Dependencies

                Internal dependencies:

                - N/A

                External dependencies:

                - N/A

                ## 8. Concerns and Questions

                - N/A

                ## 9. References

                - N/A
                """
            ),
            encoding="utf-8",
        )
        (feature / "_plan.md").write_text(
            textwrap.dedent(
                """\
                # Feature Plan: FEAT-PRETTY

                ## Meta

                - **Feature ID**: FEAT-PRETTY
                - **Base Module**: order
                - **Spec Revision**: AS-IS
                - **Created**: 2026-05-25

                ## Target Outputs

                | id | phase | target | depends_on | contract | output_files |
                | :--- | :--- | :--- | :--- | :--- | :--- |
                | D1 | Design | `modules/order/designs/model.md` | - | `core-kernel/runtime/task_contracts/design/model.yaml` | `modules/order/designs/model.md` |
                | C1 | Code | - | D1 | `core-kernel/runtime/task_contracts/code/entity.yaml` | |
                """
            ),
            encoding="utf-8",
        )
        (feature / "index.md").write_text(
            textwrap.dedent(
                """\
                # Feature Spec Index: FEAT-PRETTY

                ## Generated Spec Files

                | id | path | source item |
                | :--- | :--- | :--- |
                | `modules.order.designs.model` | `modules/order/designs/model.md` | D1 |
                """
            ),
            encoding="utf-8",
        )
        (module_designs / "model.md").write_text(
            textwrap.dedent(
                """\
                # order - Domain Model

                ## 1. Ubiquitous Language

                | code term | business term | definition | source |
                | :--- | :--- | :--- | :--- |
                | `Order` | Order | customer order | brief |

                ## 2. Entities

                | entity | field | type | constraint | invariant |
                | :--- | :--- | :--- | :--- | :--- |
                | `Order` | `id` | `Long` | required | immutable identity |

                ## 4. State Transitions

                | object | source state | trigger | target state | rule |
                | :--- | :--- | :--- | :--- | :--- |
                | `Order` | `INIT` | `review()` | `REVIEWED` | submitted only |
                """
            ),
            encoding="utf-8",
        )
        (feature / "code_contract.md").write_text(
            textwrap.dedent(
                """\
                # Code Contract: FEAT-PRETTY

                ## 0. Metadata

                - **Feature ID**: FEAT-PRETTY
                - **Contract Version**: v1

                ## 1. Entities

                | type | name | field | field type | constraint | invariant | confirmed |
                | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
                | Entity | `Order` | `id` | `Long` | required | immutable | [ ] |
                """
            ),
            encoding="utf-8",
        )
        (tests_dir / "test_cases.md").write_text("# Test Cases: FEAT-PRETTY\n", encoding="utf-8")

        site_root = tmp / "site"
        run(
            [
                sys.executable,
                "tools-skills/scripts/pretty_shiki_spec.py",
                str(ctx),
                "--output",
                str(site_root),
                "--title",
                "Pretty Test",
                "--feature",
                "FEAT-PRETTY",
                "--fail-on-broken-links",
            ]
        )
        site = site_root / "pretty_shiki_spec"
        require_file(site / "index.html")
        require_file(site / "README.html")
        require_file(site / "features" / "FEAT-PRETTY" / "overview.html")
        require_file(site / "features" / "FEAT-PRETTY" / "design.html")
        require_file(site / "features" / "FEAT-PRETTY" / "contract.html")
        require_file(site / "gaps.html")
        require_file(site / "assets" / "site.css")
        require_file(site / "assets" / "site.js")
        readme_html = (site / "README.html").read_text(encoding="utf-8")
        overview_html = (site / "features" / "FEAT-PRETTY" / "overview.html").read_text(encoding="utf-8")
        contract_html = (site / "features" / "FEAT-PRETTY" / "contract.html").read_text(encoding="utf-8")
        gaps_html = (site / "gaps.html").read_text(encoding="utf-8")
        css = (site / "assets" / "site.css").read_text(encoding="utf-8")
        for needle in [
            "L0 Human-Friendly Spec",
            "Agreement Snapshot",
            "Spec Layers",
            "L1 Consensus Sources",
            'href="features/FEAT-PRETTY/overview.html"',
            "Delivery Plan",
            "D1",
            "Code Contract View",
            "Open Placeholders",
            "[ ]",
            "--nav:",
        ]:
            if needle not in readme_html + overview_html + contract_html + gaps_html + css:
                raise AssertionError(f"pretty Shiki spec missing expected content: {needle}")


def verify_git_diff_check() -> None:
    if shutil.which("git") is None:
        return
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        log("skipping git diff whitespace check outside a git repository")
        return
    log("checking git diff whitespace")
    run(["git", "diff", "--check"])


def main() -> int:
    try:
        verify_python_and_shell()
        verify_static_text()
        verify_core_consistency()
        verify_fixture_workflow()
        verify_publish_docs()
        verify_pretty_shiki_spec()
        verify_git_diff_check()
    except Exception as exc:
        print(f"[verify] FAIL: {exc}", file=sys.stderr)
        return 1
    log("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
