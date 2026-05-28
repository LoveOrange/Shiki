"""Routing helpers shared by Shiki scripts.

This module is intentionally limited to task routing:
- inspect plan state
- determine whether an item is done
- select the next executable item
- resolve the item's task contract and workflow reference

It does not execute workflow steps. Workflow execution belongs to a dedicated
workflow-executor layer.
"""

from dataclasses import dataclass

from .evidence import code_contract_valid
from .feature_plan import is_bootstrap_plan, parse_plan
from .task_contracts import load_task_contract


class InvalidPlanTarget(ValueError):
    """Raised when a feature plan target escapes the feature scope."""


@dataclass(frozen=True)
class TaskRoute:
    """One routed plan item plus the workflow it should execute."""

    item: dict
    contract: dict
    workflow_ref: str


def _target_path(feature_dir, target):
    clean = target.strip().strip("`")
    if "#" in clean:
        clean = clean.split("#", 1)[0]
    if clean in {"", "-", "module baseline", "baseline"}:
        return None
    if clean.startswith("/") or clean.startswith("../") or "/../" in clean:
        raise InvalidPlanTarget(f"feature plan target must be relative: {clean}")
    if clean.startswith(("shiki_context/modules/", "shiki_context/project/")):
        raise InvalidPlanTarget(f"feature plan target points to baseline: {clean}")
    if clean.startswith("shiki_context/features/"):
        raise InvalidPlanTarget(f"feature plan target must be feature-root relative: {clean}")
    return feature_dir / clean


def _has_output_files(item):
    """Check if a plan item has output_files filled."""
    output = item.get("output_files", "").strip()
    if not output or output == "-":
        return False
    return not output.upper().startswith("STALE")


def _output_stale(item):
    """Return True when output_files explicitly marks the item stale."""
    return item.get("output_files", "").strip().upper().startswith("STALE")


def _contract_ref(item):
    """Return the plan row contract reference without Markdown quoting."""
    return item.get("contract", "").strip().strip("`")


def _contract_matches(item, suffix):
    return _contract_ref(item).endswith(suffix)


def item_done(feature_dir, item):
    """Best-effort completion check for plan items."""
    if _output_stale(item):
        return False

    target = item.get("target", "")
    target_path = _target_path(feature_dir, target)

    if _contract_matches(item, "design/design_init.yaml"):
        metadata, items = parse_plan(feature_dir / "_plan.md")
        base_module = metadata.get("Base Module", "")
        return base_module not in {"", "-", "[TBD]"} and not is_bootstrap_plan(items)

    if _contract_matches(item, "design/code_contract.yaml"):
        if target_path is None or not target_path.exists():
            return False
        valid, _ = code_contract_valid(feature_dir)
        return valid

    if _contract_matches(item, "merge/feature_merge.yaml"):
        return False

    # For Code items, check output_files column
    if item.get("phase") == "Code":
        return _has_output_files(item)

    # For Design items, check if target file exists
    if target_path is None:
        return False
    return target_path.exists()


def route_next_item(feature_dir):
    """Return the next executable plan item, task contract and workflow."""
    plan_path = feature_dir / "_plan.md"
    _, items = parse_plan(plan_path)
    completed = {item.get("id") for item in items if item_done(feature_dir, item)}

    for item in items:
        depends_on = item.get("depends_on", "-").strip()
        if depends_on not in {"", "-"}:
            needed = [part.strip() for part in depends_on.split(",") if part.strip()]
            # Handle range notation like "D1-D6"
            expanded = []
            for dep in needed:
                if "-" in dep and len(dep) > 2:
                    # Try to expand range like D1-D6
                    try:
                        prefix = dep[0]
                        start = int(dep[1:dep.index("-")])
                        end = int(dep[dep.index("-") + 1:].lstrip(prefix))
                        expanded.extend(f"{prefix}{i}" for i in range(start, end + 1))
                    except (ValueError, IndexError):
                        expanded.append(dep)
                else:
                    expanded.append(dep)
            if any(dep not in completed for dep in expanded):
                continue
        if item_done(feature_dir, item):
            continue
        contract = load_task_contract(item["contract"].strip("`"))
        return TaskRoute(
            item=item,
            contract=contract,
            workflow_ref=contract["workflow_ref"],
        )

    return None


def select_next_item(feature_dir):
    """Compatibility wrapper returning the next item and its task contract."""
    route = route_next_item(feature_dir)
    if route is None:
        return None, None
    return route.item, route.contract
