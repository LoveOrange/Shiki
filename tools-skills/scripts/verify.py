#!/usr/bin/env python3
"""Repository regression checks for the Shiki v4 dual-track runtime."""

from __future__ import annotations

import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMAND_NAMES = (
    "shiki-init",
    "shiki-scan",
    "shiki-new-feature",
    "shiki-status",
    "shiki-next",
    "shiki-apply",
    "shiki-modify",
    "shiki-review",
    "shiki-sync",
    "shiki-doctor",
    "shiki-fix",
    "shiki-web-spec",
)
TOOLS = {
    "codex": (".codex/prompts", ".md"),
    "claude": (".claude/commands", ".md"),
    "gemini": (".gemini/commands", ".toml"),
    "opencode": (".opencode/commands", ".md"),
}
MANAGED_MARKER = "Shiki Adapter: managed by tools-skills/scripts/install_agent_adapter.py"


def log(message: str) -> None:
    print(f"[verify] {message}")


def run(cmd: list[str], cwd: Path = ROOT, expect: int = 0, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != expect:
        raise AssertionError(
            f"command returned {result.returncode}, expected {expect}: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def require(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"required path missing: {path.relative_to(ROOT)}")


def top_level_keys(text: str) -> set[str]:
    return {
        match.group(1)
        for line in text.splitlines()
        if (match := re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s|$)", line))
    }


def verify_required_surface() -> None:
    log("required v4 surface")
    for relative in (
        "core-kernel/_lib/config.py",
        "core-kernel/_lib/context.py",
        "core-kernel/_lib/kernel.py",
        "core-kernel/_lib/task_contracts.py",
        "core-kernel/_lib/task_tools.py",
        "core-kernel/_lib/prompt_builder.py",
        "core-kernel/runtime/execution_session.md",
        "core-kernel/runtime/context_loading.md",
        "core-kernel/workflows/runner/next.md",
        "providers/codex.py",
        "providers/claude.py",
        "providers/process.py",
        "docs/v4-ideal-design.md",
        "docs/v4-architecture.md",
        "docs/v4-runtime-flows.md",
        "tests/SHIKI_FLOW_TESTS.md",
    ):
        require(ROOT / relative)
    for removed in (
        "core-kernel/_lib/workflow_executor.py",
        "core-kernel/workflows/runner/batch.md",
        "core-kernel/workflows/init/entrance.md",
        "core-kernel/workflows/init/sync.md",
        "core-kernel/workflows/test/run_and_route.md",
        "tools-skills/scripts/batch_analyze.py",
        "providers/" + "command.py",
        "providers/" + "dev" + "agent.py",
    ):
        if (ROOT / removed).exists():
            raise AssertionError(f"obsolete v3 file remains: {removed}")


def verify_python_and_shell() -> None:
    log("Python and shell syntax")
    roots = ["core-kernel", "providers", "shiki_cli", "tools-skills/scripts", "tools-skills/skills"]
    for relative in roots:
        for path in sorted((ROOT / relative).rglob("*.py")):
            py_compile.compile(str(path), doraise=True)
    for path in sorted(ROOT.rglob("*.sh")):
        if ".git" not in path.parts:
            run(["bash", "-n", str(path)])


def verify_contracts_and_workflows() -> None:
    log("Canonical/Alias Task Contracts and workflows")
    sys.path.insert(0, str(ROOT / "core-kernel"))
    from _lib.task_contracts import load_task_contract

    root = ROOT / "core-kernel" / "runtime" / "task_contracts"
    canonical_allowed = {
        "kind", "id", "stage", "goal", "inputs", "references", "output",
        "checks", "retry", "done", "workflow_ref",
    }
    for path in sorted(root.rglob("*.yaml")):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        keys = top_level_keys(text)
        contract = load_task_contract(relative)
        if "kind: alias" in text:
            if keys != {"kind", "id", "canonical"}:
                raise AssertionError(f"Alias must contain only kind/id/canonical: {relative}: {sorted(keys)}")
            if not contract.get("_canonical_ref"):
                raise AssertionError(f"Alias did not resolve: {relative}")
            continue
        required = {"kind", "id", "stage", "goal", "inputs", "workflow_ref"}
        if not required.issubset(keys):
            raise AssertionError(f"Canonical missing fields: {relative}: {sorted(required - keys)}")
        if keys - canonical_allowed:
            raise AssertionError(f"Canonical has unsupported top-level fields: {relative}: {sorted(keys - canonical_allowed)}")
        workflow = ROOT / contract["workflow_ref"]
        if not workflow.is_file():
            raise AssertionError(f"workflow_ref does not resolve: {relative}: {contract['workflow_ref']}")

    for path in sorted((ROOT / "core-kernel" / "workflows").rglob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        if "## Load" in text:
            raise AssertionError(f"Workflow duplicates Contract inputs: {path.relative_to(ROOT)}")
        if path.parent.name != "runner" and ("## Steps" not in text or "## Verification" not in text):
            raise AssertionError(f"Workflow lacks Steps/Verification: {path.relative_to(ROOT)}")


def verify_v4_semantics() -> None:
    log("dual-track and Plan semantics")
    execution = (ROOT / "core-kernel/runtime/execution_session.md").read_text(encoding="utf-8")
    for needle in (
        "CLI Automatic Track",
        "fresh Provider session",
        "Prompt Manual Track",
        "current Coding Agent session",
        "developer decides when Review runs",
    ):
        if needle not in execution:
            raise AssertionError(f"execution_session.md missing: {needle}")

    plan = (ROOT / "core-kernel/templates/feature/_plan.md").read_text(encoding="utf-8")
    if "| id | phase | target | depends_on | contract | output_files |" not in plan:
        raise AssertionError("feature Plan does not use the six-column v4 ledger")
    forbidden_columns = {"status", "evidence", "review_result"}
    header = next(line for line in plan.splitlines() if line.startswith("| id |"))
    if any(column in header for column in forbidden_columns):
        raise AssertionError("feature Plan contains v3 session-state columns")

    scan_source = (ROOT / "tools-skills/scripts/scan.py").read_text(encoding="utf-8")
    for needle in ("init/inspect_controller.yaml", "init/sync_plan.yaml", "output_files"):
        if needle not in scan_source:
            raise AssertionError(f"scan.py missing v4 routing field: {needle}")

    adapter_contract = (ROOT / "user-interface/adapters/tool_adapter_contract_v1.md").read_text(encoding="utf-8")
    for needle in ("one Kernel-prepared Task", "current Coding Agent session", "Review runs only"):
        if needle not in adapter_contract:
            raise AssertionError(f"adapter contract missing Prompt-track rule: {needle}")

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "core-kernel", ROOT / "user-interface", ROOT / "providers")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".md", ".py", ".yaml"}
    )
    legacy_provider = "Dev" + "Agent"
    for obsolete in ("adaptive execution session", "core-kernel/workflows/runner/batch.md", legacy_provider):
        if obsolete in combined:
            raise AssertionError(f"obsolete v3/internal term remains: {obsolete}")


def verify_adapter_installer(tmp: Path) -> None:
    log("Prompt-track adapter installer")
    project = tmp / "adapters"
    project.mkdir()
    command = [
        sys.executable,
        str(ROOT / "tools-skills/scripts/install_agent_adapter.py"),
        "--tool", "all",
        "--project-root", str(project),
        "--allow-outside-project",
    ]
    run(command)
    second = run(command)
    if "Created (0)" not in second.stdout or "Updated (0)" not in second.stdout:
        raise AssertionError("adapter installer is not idempotent")

    for tool, (directory, extension) in TOOLS.items():
        manifest_path = project / ".shiki" / "adapters" / tool / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {
            "collaboration_track": "prompt_manual",
            "execution_modes": ["single_task_current_session"],
            "session_owner": "developer",
            "review_owner": "developer",
        }
        for key, value in expected.items():
            if manifest.get(key) != value:
                raise AssertionError(f"{tool} manifest {key} mismatch: {manifest.get(key)!r}")
        for name in COMMAND_NAMES:
            require_project_file = project / directory / f"{name}{extension}"
            if not require_project_file.is_file():
                raise AssertionError(f"adapter command missing: {require_project_file.relative_to(project)}")
            text = require_project_file.read_text(encoding="utf-8")
            if MANAGED_MARKER not in text:
                raise AssertionError(f"managed marker missing: {require_project_file.relative_to(project)}")

    for required in (
        ".codex/skills/shiki/SKILL.md",
        ".opencode/agents/shiki-runner.md",
        ".opencode/agents/shiki-reviewer.md",
    ):
        if not (project / required).is_file():
            raise AssertionError(f"adapter extra file missing: {required}")
    for obsolete in (
        ".claude/agents/shiki-phase-wave.md",
        ".opencode/agents/shiki-phase-wave.md",
    ):
        if (project / obsolete).exists():
            raise AssertionError(f"obsolete phase-wave agent was installed: {obsolete}")

    protected = tmp / "protected"
    (protected / ".codex/prompts").mkdir(parents=True)
    user_file = protected / ".codex/prompts/shiki-next.md"
    user_file.write_text("user-owned\n", encoding="utf-8")
    blocked = run(
        [
            sys.executable,
            str(ROOT / "tools-skills/scripts/install_agent_adapter.py"),
            "--tool", "codex",
            "--project-root", str(protected),
            "--allow-outside-project",
        ],
        expect=1,
    )
    if "Blocked (1)" not in blocked.stdout or user_file.read_text(encoding="utf-8") != "user-owned\n":
        raise AssertionError("adapter installer overwrote or failed to report a user-owned file")


def write_controller(project: Path) -> None:
    path = project / "src/main/java/com/example/shop/adapter/order/web/OrderController.java"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "package com.example.shop.adapter.order.web;\n"
        "import org.springframework.web.bind.annotation.RestController;\n"
        "@RestController public class OrderController {}\n",
        encoding="utf-8",
    )


def verify_consumer_smoke(tmp: Path) -> None:
    log("consumer install, Init scan, feature bootstrap, and Kernel task next")
    project = tmp / "consumer"
    project.mkdir()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    run(
        [
            sys.executable, "-m", "shiki_cli", "install",
            "--project-root", str(project),
            "--source", str(ROOT),
            "--mode", "copy",
            "--tool", "codex",
        ],
        env=env,
    )
    write_controller(project)
    active = project / "shiki_context/workspace/active_task.md"
    text = active.read_text(encoding="utf-8").replace("[Init/Design/Code/Test/Merge]", "Init")
    active.write_text(text, encoding="utf-8")
    run([sys.executable, "shiki/tools-skills/scripts/scan.py"], cwd=project, env=env)
    plan = (project / "shiki_context/workspace/_plan.md").read_text(encoding="utf-8")
    for needle in ("inspect-001", "init/inspect_controller.yaml", "sync-plan", "init/sync_plan.yaml"):
        if needle not in plan:
            raise AssertionError(f"scan Plan missing: {needle}")
    routed = run(
        [sys.executable, "-m", "shiki_cli", "task", "next", "--project-root", str(project)],
        cwd=project,
        env=env,
    )
    if "READY: inspect-001" not in routed.stdout or "# TaskRoute" not in routed.stdout:
        raise AssertionError("Kernel task next did not prepare the first Init Task")

    provider_script = project / "fake_codex"
    provider_script.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, subprocess, sys\n"
        "pathlib.Path('provider-pids.txt').open('a', encoding='utf-8').write(str(os.getpid()) + '\\n')\n"
        "prompt = sys.stdin.read()\n"
        "if 'selected_item: inspect-001' in prompt:\n"
        "    subprocess.run([sys.executable, '-m', 'shiki_cli', 'plan', 'add-item', "
        "'--project-root', '.', '--parent', 'inspect-001', '--id', 'entrance-001', "
        "'--phase', 'Init', '--target', 'modules/order/entrances/order.md', '--module', 'order', "
        "'--depends-on', 'inspect-001', '--contract', 'init/entrance_spec.yaml'], "
        "check=True, stdout=subprocess.DEVNULL)\n"
        "print('PASS: fixture provider')\n",
        encoding="utf-8",
    )
    provider_script.chmod(0o755)
    provider_env = env.copy()
    provider_env["SHIKI_CODEX_EXECUTABLE"] = str(provider_script)
    run(
        [
            sys.executable, "-m", "shiki_cli", "scan",
            "--project-root", str(project),
            "--provider", "codex",
        ],
        cwd=project,
        env=provider_env,
    )
    pids = (project / "provider-pids.txt").read_text(encoding="utf-8").splitlines()
    if len(pids) != 2 or len(set(pids)) != 2:
        raise AssertionError(f"CLI automatic track did not isolate Task and Review sessions: {pids!r}")

    sync_task = run(
        [
            sys.executable, "-m", "shiki_cli", "task", "next",
            "--project-root", str(project), "--scope", "sync",
        ],
        cwd=project,
        env=env,
    )
    if "READY: sync-plan" not in sync_task.stdout or "--scope sync" not in sync_task.stdout:
        raise AssertionError("Prompt-track Sync did not route through the explicit Sync scope")

    run(
        [sys.executable, "-m", "shiki_cli", "new-feature", "--project-root", str(project), "--taskid", "FEAT-V4"],
        cwd=project,
        env=env,
    )
    feature_plan = (project / "shiki_context/features/FEAT-V4/_plan.md").read_text(encoding="utf-8")
    if "design/design_init.yaml" not in feature_plan or "output_files" not in feature_plan:
        raise AssertionError("new feature did not create the v4 bootstrap Plan")


def verify_commands() -> None:
    log("CLI and structural simulation")
    help_result = run([sys.executable, "-m", "shiki_cli", "--help"])
    for command in ("next", "scan", "sync", "status", "review", "task", "plan", "tool"):
        if command not in help_result.stdout:
            raise AssertionError(f"CLI help missing command: {command}")
    run([sys.executable, "tools-skills/scripts/simulate_scenarios.py"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])


def verify_public_language() -> None:
    log("public naming and language")
    roots = [ROOT / "core-kernel", ROOT / "user-interface", ROOT / "providers"]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".py", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            legacy_provider = "Dev" + "Agent"
            if "YACA" in text or legacy_provider in text:
                raise AssertionError(f"internal upstream name leaked into public framework: {path.relative_to(ROOT)}")
            if re.search(r"[\u3400-\u9fff]", text):
                raise AssertionError(f"non-English framework text remains: {path.relative_to(ROOT)}")


def main() -> int:
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    verify_required_surface()
    verify_python_and_shell()
    verify_contracts_and_workflows()
    verify_v4_semantics()
    verify_public_language()
    verify_commands()
    with tempfile.TemporaryDirectory(prefix="shiki-v4-verify-") as directory:
        tmp = Path(directory)
        verify_adapter_installer(tmp)
        verify_consumer_smoke(tmp)
    log("PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"[verify] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
