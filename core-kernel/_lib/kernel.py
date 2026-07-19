"""Routing helpers shared by Shiki scripts.

This module is intentionally limited to task routing:
- consume one parsed plan context
- determine whether an item is done
- select the next executable item
- resolve the item's task contract and workflow reference

It does not execute workflow steps. Context loading and Provider execution are
separate runtime boundaries.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .context import expand_artifact_path, resolve_artifact_path
from .feature_plan import is_bootstrap_plan, parse_plan
from .task_contracts import load_task_contract, recommend_producer


EMPTY_PLAN_MARKERS = {"", "—", "-", "pending", "not generated", "pending", "todo", "n/a", "na", "none", "null"}


class InvalidPlanTarget(ValueError):
    """Raised when a feature plan target escapes the feature scope."""


@dataclass(frozen=True)
class PlanContext:
    """One parsed Plan passed through routing and context loading."""

    path: Path
    metadata: dict
    items: tuple

    def dependencies_for(self, item):
        dependency_ids = set(_expanded_depends(item.get("depends_on", "")))
        return tuple(candidate for candidate in self.items if _item_id(candidate) in dependency_ids)


@dataclass(frozen=True)
class TaskRoute:
    """One routed plan item plus the workflow it should execute."""

    item: dict
    contract: dict
    workflow_ref: str


@dataclass(frozen=True)
class RoutingDecision:
    route: Optional[TaskRoute] = None
    recommendation: Optional[dict] = None
    blocker: str = ""


def _target_path(feature_dir, target):
    clean = target.strip().strip("`")
    if "#" in clean:
        clean = clean.split("#", 1)[0]
    if clean in {"", "—", "-", "module baseline", "baseline"}:
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
    output = item.get("output_files", "").strip().strip("`").strip()
    return output.lower() not in EMPTY_PLAN_MARKERS


def _output_files_exist(feature_dir, item):
    output = item.get("output_files", "").strip().strip("`").strip()
    if not output or output.lower() in EMPTY_PLAN_MARKERS:
        return False
    status = output.split(":", 1)[0].strip().upper()
    if status == "NOOP":
        return True
    if status in {"BLOCKED", "FAILED", "MANUAL_DECISION"}:
        return False

    project_root = _project_root(feature_dir)
    for raw_value in output.split(","):
        value = raw_value.strip().strip("`")
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            if value.startswith("shiki_context/"):
                path = project_root / value
            elif value.startswith(("workspace/", "project/", "features/", "constitution/")):
                path = project_root / "shiki_context" / value
            elif value.startswith(("modules/", "tests/")):
                if Path(feature_dir).parent.name == "features":
                    path = Path(feature_dir) / value
                else:
                    path = project_root / "shiki_context" / value
            elif value in {"_plan.md", "index.md", "design_brief.md", "code_contract.md"}:
                path = Path(feature_dir) / value
            else:
                path = project_root / value
        if not path.exists():
            return False
    return True


def _contract_ref(item):
    """Return the plan row contract reference without Markdown quoting."""
    return item.get("contract", "").strip().strip("`")


def _item_id(item):
    return item.get("id", "").strip().strip("`")


def _contract_id(item):
    ref = _contract_ref(item)
    if ref.startswith("init."):
        return ref.split(".", 1)[1]
    return Path(ref).stem


def _contract_matches(item, suffix):
    return _contract_ref(item).endswith(suffix)


def _expanded_depends(depends_on):
    needed = [part.strip().strip("`") for part in depends_on.split(",") if part.strip().strip("`")]
    expanded = []
    for dep in needed:
        if dep in {"", "—", "-"}:
            continue
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
    depends_on = item.get("depends_on", "—").strip()
    if depends_on in {"", "—", "-"}:
        return True
    return all(dep in completed for dep in _expanded_depends(depends_on))


def _validate_item_target(feature_dir, item):
    _target_path(feature_dir, item.get("target", ""))


def item_done(feature_dir, item, plan_context=None):
    """Best-effort completion check for plan items."""
    if Path(feature_dir).parent.name == "features" and _contract_matches(item, "design/design_init.yaml"):
        if plan_context is None:
            metadata, items = parse_plan(feature_dir / "_plan.md")
        else:
            metadata, items = plan_context.metadata, plan_context.items
        base_module = metadata.get("Base Module", "")
        return base_module not in {"", "—", "-", "[TBD]"} and not is_bootstrap_plan(items)

    if _contract_id(item) == "inspect_controller":
        output = item.get("output_files", "").strip().strip("`").strip()
        if output.split(":", 1)[0].strip().upper() == "NOOP":
            return True
        if not _output_files_exist(feature_dir, item):
            return False
        if plan_context is None:
            _, items = parse_plan(Path(feature_dir) / "_plan.md")
        else:
            items = plan_context.items
        item_id = item.get("id", "").strip().strip("`")
        return any(
            _contract_id(candidate) == "entrance_spec"
            and item_id in _expanded_depends(candidate.get("depends_on", ""))
            for candidate in items
        )

    return _output_files_exist(feature_dir, item)


def _project_root(feature_dir):
    path = Path(feature_dir).resolve()
    for parent in [path, *path.parents]:
        if (parent / "shiki_context").is_dir():
            return parent
    return path.parents[2]


def _missing_required_inputs(feature_dir, item, contract, plan_context=None):
    project_root = _project_root(feature_dir)
    missing = []
    for value in contract.get("required_inputs", []):
        metadata = plan_context.metadata if plan_context is not None else None
        path = resolve_artifact_path(project_root, feature_dir, item, value, plan_metadata=metadata)
        if path is not None and not expand_artifact_path(path):
            missing.append(value)
            continue
        if plan_context is not None:
            owner = recommend_producer(value)
            producer_item = (
                _plan_item_for_contract(plan_context.items, owner.recommended_contract)
                if owner.status == "recommended"
                else None
            )
            if producer_item is not None and not item_done(feature_dir, producer_item, plan_context):
                missing.append(value)
    return missing


def _plan_item_for_contract(items, contract_ref):
    suffix = contract_ref.strip().strip("`")
    matches = [item for item in items if _contract_ref(item).endswith(suffix)]
    return matches[0] if len(matches) == 1 else None


def _parsed_plan_context(feature_dir):
    path = Path(feature_dir) / "_plan.md"
    metadata, items = parse_plan(path)
    return PlanContext(path=path, metadata=metadata, items=tuple(items))


def route_next_decision(feature_dir, plan_context=None):
    """Route a ready task or explain the required producer/blocker."""
    plan_context = plan_context or _parsed_plan_context(feature_dir)
    items = plan_context.items
    completion = {_item_id(item): item_done(feature_dir, item, plan_context) for item in items}
    completed = {item_id for item_id, done in completion.items() if done}

    for item in items:
        if not _dependencies_satisfied(item, completed) or completion[_item_id(item)]:
            continue
        _validate_item_target(feature_dir, item)
        contract = load_task_contract(item["contract"].strip("`"))
        missing = _missing_required_inputs(feature_dir, item, contract, plan_context)
        if not missing:
            return RoutingDecision(
                route=TaskRoute(item=item, contract=contract, workflow_ref=contract["workflow_ref"])
            )

        recommendations = [recommend_producer(value) for value in missing]
        ambiguous = [rec for rec in recommendations if rec.status == "manual_decision"]
        unavailable = [rec for rec in recommendations if rec.status == "blocked"]
        if ambiguous:
            rec = ambiguous[0]
            return RoutingDecision(
                recommendation={
                    "blocked_task": _item_id(item),
                    "missing_artifact": rec.missing_artifact,
                    "alternatives": list(rec.producers),
                },
                blocker="MANUAL_DECISION: multiple producers for required input",
            )
        if unavailable:
            rec = unavailable[0]
            return RoutingDecision(
                recommendation={
                    "blocked_task": _item_id(item),
                    "missing_artifact": rec.missing_artifact,
                    "alternatives": [],
                },
                blocker="BLOCKED: missing required input has no producer",
            )

        rec = recommendations[0]
        producer_item = _plan_item_for_contract(items, rec.recommended_contract)
        recommendation = {
            "blocked_task": _item_id(item),
            "missing_artifact": rec.missing_artifact,
            "recommended_contract": rec.recommended_contract,
            "recommended_task": _item_id(producer_item) if producer_item else "",
            "reason": "required artifact is missing",
            "alternatives": [],
        }
        if producer_item is not None:
            if _dependencies_satisfied(producer_item, completed):
                producer_contract = load_task_contract(_contract_ref(producer_item))
                return RoutingDecision(
                    route=TaskRoute(
                        item=producer_item,
                        contract=producer_contract,
                        workflow_ref=producer_contract["workflow_ref"],
                    ),
                    recommendation=recommendation,
                )
        return RoutingDecision(
            recommendation=recommendation,
            blocker="NEXT_TASK_RECOMMENDATION: generate missing required input",
        )

    return RoutingDecision()


def route_next_item(feature_dir):
    """Return the next executable plan item, task contract and workflow."""
    return route_next_decision(feature_dir).route


def route_item(feature_dir, item_id):
    """Return a route for a specified item if it exists and dependencies are met."""
    return route_item_decision(feature_dir, item_id).route


def route_item_decision(feature_dir, item_id, plan_context=None):
    """Route one selected item and enforce its required input contract."""
    plan_context = plan_context or _parsed_plan_context(feature_dir)
    items = plan_context.items
    completed = {
        _item_id(item)
        for item in items
        if item_done(feature_dir, item, plan_context)
    }
    for item in items:
        if _item_id(item) != item_id:
            continue
        if not _dependencies_satisfied(item, completed):
            return RoutingDecision(blocker=f"BLOCKED: selected item {item_id} depends_on is unsatisfied")
        _validate_item_target(feature_dir, item)
        contract = load_task_contract(item["contract"].strip("`"))
        missing = _missing_required_inputs(feature_dir, item, contract, plan_context)
        if missing:
            rec = recommend_producer(missing[0])
            recommendation = {
                "blocked_task": item_id,
                "missing_artifact": rec.missing_artifact,
                "recommended_contract": rec.recommended_contract,
                "alternatives": list(rec.producers),
            }
            if rec.status == "recommended":
                producer_item = _plan_item_for_contract(items, rec.recommended_contract)
                recommendation["recommended_task"] = _item_id(producer_item) if producer_item else ""
                if producer_item is not None and _dependencies_satisfied(producer_item, completed):
                    producer_contract = load_task_contract(_contract_ref(producer_item))
                    return RoutingDecision(
                        route=TaskRoute(
                            item=producer_item,
                            contract=producer_contract,
                            workflow_ref=producer_contract["workflow_ref"],
                        ),
                        recommendation=recommendation,
                    )
                return RoutingDecision(
                    recommendation=recommendation,
                    blocker="NEXT_TASK_RECOMMENDATION: generate missing required input",
                )
            if rec.status == "manual_decision":
                return RoutingDecision(
                    recommendation=recommendation,
                    blocker="MANUAL_DECISION: multiple producers for required input",
                )
            return RoutingDecision(
                recommendation=recommendation,
                blocker="BLOCKED: missing required input has no producer",
            )
        return RoutingDecision(
            route=TaskRoute(
                item=item,
                contract=contract,
                workflow_ref=contract["workflow_ref"],
            )
        )
    return RoutingDecision(blocker=f"BLOCKED: selected item {item_id} does not exist")


def select_next_item(feature_dir):
    """Compatibility wrapper returning the next item and its task contract."""
    route = route_next_item(feature_dir)
    if route is None:
        return None, None
    return route.item, route.contract


def select_item(feature_dir, item_id):
    """Compatibility wrapper returning a specified item and its task contract."""
    route = route_item(feature_dir, item_id)
    if route is None:
        return None, None
    return route.item, route.contract
