"""Project configuration used by the Shiki runtime."""

from pathlib import Path

from .task_contracts import _load_yaml


VALID_GRANULARITIES = {"task", "phase", "feature"}


def load_project_config(project_root):
    """Load shiki.config.yaml from a project root."""
    path = Path(project_root) / "shiki.config.yaml"
    if not path.exists():
        return {}
    data = _load_yaml(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def active_tech_stacks(project_root):
    """Return the configured project-owned tech contract names."""
    stacks = load_project_config(project_root).get("tech_stacks", [])
    if isinstance(stacks, str):
        stacks = [stacks]
    return tuple(str(stack).strip() for stack in stacks if str(stack).strip())


def orchestration_granularity(project_root):
    """Return task, phase, or feature; task is the stable default."""
    orchestrate = load_project_config(project_root).get("orchestrate", {})
    value = orchestrate.get("granularity", "task") if isinstance(orchestrate, dict) else "task"
    value = str(value).strip().lower()
    if value not in VALID_GRANULARITIES:
        raise ValueError(
            "shiki.config.yaml orchestrate.granularity must be one of: "
            + ", ".join(sorted(VALID_GRANULARITIES))
        )
    return value


def configured_tech_contract_paths(project_root):
    """Return project-owned active tech contract directories."""
    root = Path(project_root) / "shiki_context" / "constitution" / "tech_contracts"
    return tuple(root / stack for stack in active_tech_stacks(project_root))
