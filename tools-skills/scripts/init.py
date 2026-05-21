#!/usr/bin/env python3
"""
Shiki Context Initializer

Initializes the shiki_context/ directory by copying templates and project rules
from the Shiki framework.
Cross-platform (Windows/Linux/macOS), zero external dependencies (Python 3.6+).

Usage:
    python shiki/tools-skills/scripts/init.py                     # Default: creates shiki_context/ next to shiki/
    python shiki/tools-skills/scripts/init.py --target ./my_ctx    # Custom target directory
    python shiki/tools-skills/scripts/init.py --force              # Overwrite existing files
"""

import os
import sys
import shutil
import argparse
from pathlib import Path



def get_shiki_root():
    """Locate the Shiki framework root."""
    return Path(__file__).resolve().parents[2]


def get_template_dir(shiki_root):
    """Get the template directory path."""
    template_dir = shiki_root / "core-kernel" / "templates"
    if not template_dir.exists():
        print(f"ERROR: Template directory not found: {template_dir}")
        sys.exit(1)
    return template_dir


def copy_config(shiki_root, project_root, force=False):
    """
    Copy shiki.config.yaml from shiki/ to project root if not already present.
    Returns (created: bool, path: Path).
    """
    src = shiki_root / "shiki.config.yaml"
    dst = project_root / "shiki.config.yaml"
    if not src.exists():
        return False, dst
    if dst.exists() and not force:
        return False, dst
    shutil.copy2(str(src), str(dst))
    return True, dst


def strip_comment(value):
    """Remove simple YAML comments from a scalar value."""
    if "#" not in value:
        return value.strip()
    return value.split("#", 1)[0].strip()


def parse_simple_yaml(path):
    """Parse the small shiki.config.yaml subset needed by init.py."""
    result = {}
    current_key = None
    if not path.exists():
        return result
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- ") and current_key:
            result.setdefault(current_key, []).append(strip_comment(stripped[2:]).strip("\"'"))
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        current_key = key.strip()
        value = strip_comment(value).strip("\"'")
        result[current_key] = value if value else []
    return result


def selected_tech_stacks(config_path):
    """Return configured project-owned tech contracts."""
    config = parse_simple_yaml(config_path)
    stacks = config.get("tech_stacks", [])
    if isinstance(stacks, str):
        stacks = [stacks]
    return [stack for stack in stacks if stack]


def copy_file(src, dst, created, skipped, force=False):
    """Copy one file unless it already exists."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        skipped.append(str(dst))
        return
    shutil.copy2(str(src), str(dst))
    created.append(str(dst))


def copy_tech_contracts(shiki_root, target_dir, tech_stacks, force=False):
    """Copy configured tech contracts into shiki_context for project ownership."""
    created = []
    skipped = []
    contracts_src = shiki_root / "tech-stacks" / "tech-contracts"
    contracts_dst = target_dir / "constitution" / "tech_contracts"
    if not contracts_src.exists():
        return created, skipped

    readme_src = contracts_src / "README.md"
    if readme_src.exists():
        copy_file(readme_src, contracts_dst / "README.md", created, skipped, force=force)

    for stack in tech_stacks:
        stack_dir = contracts_src / stack
        stack_file = contracts_src / (stack + ".md")
        if stack_dir.exists() and stack_dir.is_dir():
            for src in sorted(stack_dir.rglob("*")):
                if src.is_file():
                    copy_file(src, contracts_dst / stack / src.relative_to(stack_dir), created, skipped, force=force)
            continue
        if stack_file.exists():
            copy_file(stack_file, contracts_dst / stack_file.name, created, skipped, force=force)
            continue
        print(f"WARN: tech contract not found: {stack}")
    return created, skipped


def copy_templates(template_dir, target_dir, force=False):
    """Copy templates to target directory. Returns list of created files."""
    created = []
    skipped = []

    # Copy project templates into project/.
    project_src = template_dir / "project"
    project_dst = target_dir / "project"
    if project_src.exists():
        project_dst.mkdir(parents=True, exist_ok=True)
        for f in project_src.iterdir():
            if f.is_file():
                dst = project_dst / f.name
                if dst.exists() and not force:
                    skipped.append(str(dst))
                else:
                    shutil.copy2(str(f), str(dst))
                    created.append(str(dst))

    # Create collection roots used by the target context-store layout.
    (target_dir / "modules").mkdir(parents=True, exist_ok=True)
    (target_dir / "features").mkdir(parents=True, exist_ok=True)

    # Copy workspace templates into workspace/.
    workspace_src = template_dir / "workspace"
    workspace_dst = target_dir / "workspace"
    if workspace_src.exists():
        workspace_dst.mkdir(parents=True, exist_ok=True)
        for f in workspace_src.iterdir():
            if f.is_file():
                dst = workspace_dst / f.name
                if dst.exists() and not force:
                    skipped.append(str(dst))
                else:
                    shutil.copy2(str(f), str(dst))
                    created.append(str(dst))

    return created, skipped



def print_report(target_dir, created, skipped, config_created, config_path, tech_stacks):
    """Print initialization report."""
    print("")
    print("=" * 55)
    print("  Shiki Initialized")
    print("=" * 55)

    if config_created:
        print(f"  + {config_path}  <- edit base_package")
    else:
        print(f"  ~ {config_path}  (already exists, skipped)")

    print(f"  Context dir: {target_dir}")
    if tech_stacks:
        print(f"  Tech contracts: {', '.join(tech_stacks)}")

    if created:
        print(f"\n  Created ({len(created)} files):")
        for f in created:
            print(f"    + {f}")

    if skipped:
        print(f"\n  Skipped ({len(skipped)} files, already exist):")
        for f in skipped:
            print(f"    ~ {f}")
        print("  Use --force to overwrite existing files.")

    print("")
    print("  Next steps:")
    print("    1. Edit shiki.config.yaml in the project root and set base_package.")
    print("    2. Use CHEATSHEET.md prompts with your AI coding agent.")
    print("")
    print("  Note: keep files under shiki/ read-only in consumer projects.")
    print("        Project-owned configuration lives in shiki.config.yaml and shiki_context/.")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        description="Initialize shiki_context/ directory from Shiki templates."
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target directory for shiki_context/ (default: ../shiki_context relative to Shiki root)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files"
    )
    args = parser.parse_args()

    shiki_root    = get_shiki_root()
    project_root = shiki_root.parent
    template_dir = get_template_dir(shiki_root)

    if args.target:
        target_dir = Path(args.target).resolve()
    else:
        target_dir = project_root / "shiki_context"

    print(f"Shiki root:    {shiki_root}")
    print(f"Project root: {project_root}")
    print(f"Context dir:  {target_dir}")

    config_created, config_path = copy_config(shiki_root, project_root, force=args.force)
    created, skipped = copy_templates(template_dir, target_dir, force=args.force)
    tech_stacks = selected_tech_stacks(config_path)
    contract_created, contract_skipped = copy_tech_contracts(shiki_root, target_dir, tech_stacks, force=args.force)
    created.extend(contract_created)
    skipped.extend(contract_skipped)
    print_report(target_dir, created, skipped, config_created, config_path, tech_stacks)


if __name__ == "__main__":
    main()
