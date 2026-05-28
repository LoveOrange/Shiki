#!/usr/bin/env python3
"""
Shiki Feature Initializer.

Creates a feature workspace under shiki_context/features/[taskid]/ and prepares the
bootstrap lifecycle files required by the kernel-first execution path.
"""

import argparse
import sys
from pathlib import Path

SHIKI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SHIKI_ROOT / "core-kernel"))

from _lib.feature_plan import render_bootstrap_plan, today_iso
from _lib.paths import get_context_dir, get_shiki_root


def copy_feature_template_file(template_path, destination, task_id):
    """Copy one feature lifecycle template and replace placeholders."""
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("[FEAT-ID]", task_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def copy_feature_template_tree(template_dir, destination_dir, task_id):
    """Instantiate the feature template directory into a feature workspace."""
    copied = []
    for template_path in sorted(path for path in template_dir.rglob("*") if path.is_file()):
        relative = template_path.relative_to(template_dir)
        if relative.as_posix() in {"design_brief.md", "code_contract.md"}:
            continue
        copy_feature_template_file(template_path, destination_dir / relative, task_id)
        copied.append(str(relative))
    return copied


def create_feature(context_dir, shiki_root, task_id):
    """Create a feature workspace with lifecycle templates and bootstrap plan."""
    feat_dir = context_dir / "features" / task_id
    feature_template_dir = shiki_root / "core-kernel" / "templates" / "feature"
    brief_template = feature_template_dir / "design_brief.md"

    if feat_dir.exists():
        print(f"ERROR: Feature directory already exists: {feat_dir}")
        sys.exit(1)

    if not brief_template.exists():
        print(f"ERROR: design_brief.md template not found at {brief_template}")
        sys.exit(1)
    if not feature_template_dir.exists():
        print(f"ERROR: feature lifecycle templates not found at {feature_template_dir}")
        sys.exit(1)

    feat_dir.mkdir(parents=True)

    brief_content = brief_template.read_text(encoding="utf-8")
    today = today_iso()
    brief_content = brief_content.replace("# Design Brief: [Feature Name]", f"# Design Brief: {task_id}")
    brief_content = brief_content.replace("**Date**: [___]", f"**Date**: {today}")
    brief_path = feat_dir / "design_brief.md"
    brief_path.write_text(brief_content, encoding="utf-8")
    created_files = ["design_brief.md"]

    created_files.extend(copy_feature_template_tree(feature_template_dir, feat_dir, task_id))

    plan_path = feat_dir / "_plan.md"
    plan_path.write_text(render_bootstrap_plan(task_id, today), encoding="utf-8")

    return feat_dir, brief_path, plan_path, sorted(set(created_files))


def print_report(feat_dir, created_files, task_id):
    """Print creation report."""
    print("")
    print("=" * 55)
    print("  Feature Created")
    print("=" * 55)
    print(f"  Task ID: {task_id}")
    print(f"  Dir:     {feat_dir}")
    for relative in created_files:
        print(f"  + {relative}")
    print("")
    print("  Next steps:")
    print("    1. Fill in design_brief.md.")
    print("    2. Use next to run design_init and expand the plan.")
    print("    3. Follow the plan through Design -> Code -> Test -> Merge.")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new feature directory with bootstrap lifecycle files."
    )
    parser.add_argument(
        "--taskid",
        "-t",
        type=str,
        required=True,
        help="Task ID from requirement platform, e.g. FEAT-001 or JIRA-1234",
    )
    args = parser.parse_args()

    shiki_root = get_shiki_root()
    context_dir = get_context_dir()
    if not context_dir.exists():
        print(f"ERROR: shiki_context/ not found: {context_dir}")
        print("       Run 'python shiki/tools-skills/scripts/init.py' first.")
        return 1

    feat_dir, _, _, created_files = create_feature(context_dir, shiki_root, args.taskid)
    print_report(feat_dir, created_files, args.taskid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
