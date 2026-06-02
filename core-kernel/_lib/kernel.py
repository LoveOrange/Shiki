"""Routing helpers shared by Shiki scripts.

This module is intentionally limited to task routing:
- inspect plan state
- determine whether an item is done
- select the next executable item or safe explicit batch
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
    status = item.get("status", "").strip().upper()
    output = item.get("output_files", "").strip().upper()
    return status == "STALE" or output.startswith("STALE")


def _status_value(item):
    """Return normalized plan status when the status column exists."""
    return item.get("status", "").strip().upper()


def _contract_ref(item):
    """Return the plan row contract reference without Markdown quoting."""
    return item.get("contract", "").strip().strip("`")


def _contract_matches(item, suffix):
    return _contract_ref(item).endswith(suffix)


def _expanded_dependencies(depends_on):
    """Expand comma dependencies, including simple ranges like D1-D6."""
    if depends_on not in {"", "-"}:
        needed = [part.strip() for part in depends_on.split(",") if part.strip()]
    else:
        needed = []
    expanded = []
    for dep in needed:
        if "-" in dep and len(dep) > 2:
            try:
                prefix = dep[0]
                start = int(dep[1:dep.index("-")])
                end = int(dep[dep.index("-") + 1:].lstrip(prefix))
                expanded.extend(f"{prefix}{i}" for i in range(start, end + 1))
            except (ValueError, IndexError):
                expanded.append(dep)
        else:
            expanded.append(dep)
    return expanded


def _dependencies_satisfied(item, completed):
    depends_on = item.get("depends_on", "-").strip()
    return all(dep in completed for dep in _expanded_dependencies(depends_on))


def _blocked_output(item):
    status = _status_value(item)
    output = item.get("output_files", "").strip().upper()
    return (
        status in {"BLOCKED", "MANUAL_DECISION", "VERIFICATION_FAILED"}
        or output.startswith("BLOCKED")
        or output.startswith("MANUAL_DECISION")
        or output.startswith("VERIFICATION_FAILED")
    )


def _status_done(item):
    return _status_value(item) == "DONE"


def item_done(feature_dir, item):
    """Best-effort completion check for plan items."""
    if _output_stale(item):
        return False
    if _status_done(item):
        return True

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
    completed = {
        item.get("id")
        for item in items
        if not _blocked_output(item) and item_done(feature_dir, item)
    }

    for item in items:
        if not _dependencies_satisfied(item, completed):
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


def route_batch_items(feature_dir, max_items=3, allow_phase_crossing=False):
    """Return a safe ordered batch of executable plan items.

    The returned routes are still atomic. Callers execute each route through the
    normal workflow executor and update output_files before advancing.
    """
    if max_items < 1:
        return []

    plan_path = feature_dir / "_plan.md"
    _, items = parse_plan(plan_path)
    completed = {
        item.get("id")
        for item in items
        if not _blocked_output(item) and item_done(feature_dir, item)
    }
    routes = []
    batch_completed = set(completed)
    batch_phase = None

    for item in items:
        item_id = item.get("id")
        if _blocked_output(item):
            break
        if item_id in batch_completed and item_done(feature_dir, item):
            continue
        if item.get("phase") == "Merge":
            break
        if not _dependencies_satisfied(item, batch_completed):
            continue
        if item_done(feature_dir, item):
            batch_completed.add(item_id)
            continue

        phase = item.get("phase", "")
        if batch_phase is None:
            batch_phase = phase
        elif phase != batch_phase and not allow_phase_crossing:
            break

        contract = load_task_contract(item["contract"].strip("`"))
        routes.append(TaskRoute(
            item=item,
            contract=contract,
            workflow_ref=contract["workflow_ref"],
        ))
        batch_completed.add(item_id)
        if len(routes) >= max_items:
            break

    return routes


def select_next_item(feature_dir):
    """Compatibility wrapper returning the next item and its task contract."""
    route = route_next_item(feature_dir)
    if route is None:
        return None, None
    return route.item, route.contract
