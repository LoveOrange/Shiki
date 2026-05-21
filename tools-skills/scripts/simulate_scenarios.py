#!/usr/bin/env python3
"""
Lightweight Shiki workflow simulation.

This script does not call an LLM or generate code. It checks that the repository
contains the expected workflow, task-contract, template, and tech-contract
surfaces for a minimal end-to-end run.
"""

import sys
from pathlib import Path

SHIKI_ROOT = Path(__file__).resolve().parents[2]

errors: list[str] = []
warnings: list[str] = []
passed: list[str] = []


def check(condition: bool, message: str, warn_only: bool = False) -> None:
    if condition:
        passed.append(f"PASS {message}")
    elif warn_only:
        warnings.append(f"WARN {message}")
    else:
        errors.append(f"FAIL {message}")


def load_yaml_lite(path: Path) -> dict[str, str]:
    """Minimal YAML loader that only extracts top-level key/value pairs."""
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#") and not line.startswith("-"):
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip()
    return data


def test_happy_path() -> None:
    print("\nScenario 1: full feature path")
    template_dir = SHIKI_ROOT / "core-kernel" / "templates" / "feature"
    for name in ["_plan.md", "design_brief.md", "code_contract.md", "index.md"]:
        check((template_dir / name).exists(), f"feature template exists: {name}")

    cheatsheet = SHIKI_ROOT / "docs" / "CHEATSHEET.md"
    check(cheatsheet.exists(), "docs/CHEATSHEET.md exists")
    if cheatsheet.exists():
        content = cheatsheet.read_text(encoding="utf-8")
        for heading in [
            "## 1. scan",
            "## 2. new feature",
            "## 3. status",
            "## 4. apply",
            "## 5. review",
            "## 6. modify",
        ]:
            check(heading in content, f"docs/CHEATSHEET.md contains {heading}")

    expected = {
        "design": [
            "design_init",
            "model",
            "persistence",
            "acl",
            "component",
            "entrance_spec",
            "flow",
            "code_contract",
        ],
        "code": ["entity", "interface_skeletons", "feature_logic", "infrastructure", "adapter"],
        "merge": ["feature_merge"],
    }
    for phase, names in expected.items():
        for name in names:
            workflow = SHIKI_ROOT / "core-kernel" / "workflows" / phase / f"{name}.md"
            contract = SHIKI_ROOT / "core-kernel" / "runtime" / "task_contracts" / phase / f"{name}.yaml"
            check(workflow.exists(), f"workflow exists: {phase}/{name}")
            check(contract.exists(), f"task contract exists: {phase}/{name}")
            if contract.exists():
                ref = load_yaml_lite(contract).get("workflow_ref", "")
                check(bool(ref) and (SHIKI_ROOT / ref).exists(), f"workflow_ref resolves: {phase}/{name}")
            if workflow.exists():
                text = workflow.read_text(encoding="utf-8")
                for heading in ["## Load", "## Steps", "## Verification"]:
                    check(heading in text, f"{phase}/{name} has {heading}", warn_only=True)


def test_tech_stack_contracts() -> None:
    print("\nScenario 2: tech stack contracts")
    config = SHIKI_ROOT / "shiki.config.yaml"
    check(config.exists(), "shiki.config.yaml exists")
    if config.exists():
        check("java/ddd-spring" in config.read_text(encoding="utf-8"), "default stack is hierarchical")

    pack_dir = SHIKI_ROOT / "tech-stacks" / "tech-contracts" / "java" / "ddd-spring"
    for name in ["naming.md", "layering.md", "exception.md", "persistence.md", "acl.md"]:
        check((pack_dir / name).exists(), f"java/ddd-spring slice exists: {name}")


def test_public_surface() -> None:
    print("\nScenario 3: public repository surface")
    for removed in ["legacy", "shiki_context", ".claude"]:
        check(not (SHIKI_ROOT / removed).exists(), f"{removed}/ is not part of the public source surface")
    check((SHIKI_ROOT / "tests" / "fixtures" / "java-ddd-spring-sample").exists(), "generic Java fixture exists")


def test_context_budget() -> None:
    print("\nScenario 4: context budget")
    load_files = [
        "core-kernel/workflows/design/model.md",
        "tech-stacks/tech-contracts/java/ddd-spring/naming.md",
        "core-kernel/runtime/task_contracts/design/model.yaml",
        "core-kernel/runtime/context_loading.md",
    ]
    total = 4500
    for relative in load_files:
        path = SHIKI_ROOT / relative
        if path.exists():
            total += path.stat().st_size
    check(total < 15360, f"estimated model-design context is below 15 KB ({total} bytes)")


def print_report() -> None:
    print("\nSIMULATION RESULTS")
    print(f"Passed: {len(passed)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errors: {len(errors)}")
    for item in warnings:
        print(item)
    for item in errors:
        print(item)


def main() -> int:
    print("Shiki workflow simulation")
    test_happy_path()
    test_tech_stack_contracts()
    test_public_surface()
    test_context_budget()
    print_report()
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
