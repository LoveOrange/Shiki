#!/usr/bin/env python3
"""Lightweight structural simulation for the Shiki v4 public workflow."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []
passed: list[str] = []


def check(condition: bool, message: str) -> None:
    (passed if condition else errors).append(("PASS " if condition else "FAIL ") + message)


def test_contract_workflows() -> None:
    contract_root = ROOT / "core-kernel" / "runtime" / "task_contracts"
    for path in sorted(contract_root.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(contract_root).as_posix()
        if "kind: alias" in text:
            check("canonical:" in text, f"Alias has Canonical reference: {relative}")
            check("workflow_ref:" not in text, f"Alias stays minimal: {relative}")
            continue
        refs = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("workflow_ref:")]
        check(len(refs) == 1, f"Canonical has one workflow_ref: {relative}")
        if refs:
            check((ROOT / refs[0]).is_file(), f"workflow_ref resolves: {relative}")


def test_dual_tracks() -> None:
    runtime = (ROOT / "core-kernel" / "runtime" / "execution_session.md").read_text(encoding="utf-8")
    check("CLI Automatic Track" in runtime, "CLI automatic track is documented")
    check("Prompt Manual Track" in runtime, "Prompt manual track is documented")
    check((ROOT / "providers" / "codex.py").is_file(), "Codex CLI Provider exists")
    check((ROOT / "providers" / "claude.py").is_file(), "Claude CLI Provider exists")
    check(not (ROOT / "core-kernel" / "workflows" / "runner" / "batch.md").exists(), "legacy batch workflow is absent")
    check(not (ROOT / "core-kernel" / "_lib" / "workflow_executor.py").exists(), "legacy workflow executor is absent")


def test_templates_and_tools() -> None:
    plan = (ROOT / "core-kernel" / "templates" / "feature" / "_plan.md").read_text(encoding="utf-8")
    check("| id | phase | target | depends_on | contract | output_files |" in plan, "feature Plan uses v4 ledger columns")
    active = (ROOT / "core-kernel" / "templates" / "workspace" / "active_task.md").read_text(encoding="utf-8")
    check("`next`: auto" in active, "active task supports automatic routing")
    for module in ["config.py", "context.py", "task_contracts.py", "task_tools.py", "kernel.py"]:
        check((ROOT / "core-kernel" / "_lib" / module).is_file(), f"Kernel helper exists: {module}")


def main() -> int:
    print("Shiki v4 workflow simulation")
    test_contract_workflows()
    test_dual_tracks()
    test_templates_and_tools()
    for item in passed:
        print(item)
    for item in errors:
        print(item)
    print(f"Passed: {len(passed)}; Errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
