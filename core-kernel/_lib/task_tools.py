"""Deterministic Kernel tools shared by CLI and Prompt-driven agents."""

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .context import build_context_envelope, expand_artifact_path, resolve_artifact_path
from .kernel import PlanContext, TaskRoute, _target_path, item_done, route_item_decision, route_next_decision
from .markdown import metadata_value
from .task_contracts import load_task_contract


PLAN_FIELDS = ("id", "phase", "target", "depends_on", "contract", "output_files")
STOP_OUTPUT_STATUSES = {"BLOCKED", "FAILED", "MANUAL_DECISION", "CHANGE_REQUEST"}
INIT_BOOTSTRAP_TASK_ID = "init-plan"
SYNC_BOOTSTRAP_TASK_ID = "sync-plan"
INIT_BOOTSTRAP_CONTRACT_IDS = {"inspect_controller", "plan", "sync_plan"}
PLAN_SEPARATOR_RE = re.compile(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$")


def _clean(value):
    return str(value or "").strip().strip("`").strip()


def _blocker_message(value):
    return value[len("BLOCKED: ") :] if value.startswith("BLOCKED: ") else value


def _item_id(item):
    return _clean(item.get("id", ""))


def _contract_ref(item):
    return _clean(item.get("contract", ""))


def _plan_item(items, task_id):
    matches = [item for item in items if _item_id(item) == task_id]
    return matches[0] if len(matches) == 1 else None


def _scope_kind(scope_dir, requested=""):
    if requested:
        return requested
    path = Path(scope_dir)
    if path.parent.name == "features":
        return "feature"
    if path.name == "workspace":
        return "init"
    return "plan"


def _active_task_field(project_root, field):
    path = Path(project_root) / "shiki_context" / "workspace" / "active_task.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    patterns = [
        rf"^\s*-\s+`{re.escape(field)}`:\s*`?([^`\n]+)`?",
        rf"^\s*-\s+\*\*.*{re.escape(field)}.*\*\*:\s*`?([^`\n]+)`?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.M | re.I)
        if match:
            return _clean(match.group(1))
    return ""


def _contract_id(item):
    ref = _contract_ref(item)
    if ref.startswith("init."):
        return ref.split(".", 1)[1]
    return Path(ref).stem


def _empty_plan_context(plan_path):
    return PlanContext(path=Path(plan_path), metadata={}, items=())


def _plan_metadata(lines):
    text = "\n".join(lines)
    return {
        key: metadata_value(text, key)
        for key in ("Feature ID", "Base Module", "Spec Revision", "Contract Version", "Created")
    }


def _plan_signature(state, plan_context):
    payload = {
        "state": state,
        "metadata": plan_context.metadata,
        "items": list(plan_context.items),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _validate_scope_plan(project_root, scope_dir, scope_kind, plan_path=None):
    plan_path = Path(plan_path or (Path(scope_dir) / "_plan.md"))
    if not plan_path.is_file():
        return "missing", _empty_plan_context(plan_path), ""
    try:
        table = _plan_table(plan_path)
    except ValueError as exc:
        return "blocked", _empty_plan_context(plan_path), f"BLOCKED: {exc}"

    missing_headers = [field for field in PLAN_FIELDS if field not in table.headers]
    if missing_headers:
        return (
            "blocked",
            _empty_plan_context(plan_path),
            "BLOCKED: plan Target Outputs table missing required columns: " + ", ".join(missing_headers),
        )

    rows = []
    for index in range(table.row_start, table.row_end):
        stripped = table.lines[index].strip()
        if not stripped.startswith("|"):
            continue
        cells = _table_cells(stripped)
        if len(cells) != len(table.headers):
            row_id = _clean(cells[0]) if cells else f"#{index - table.row_start + 1}"
            return (
                "blocked",
                _empty_plan_context(plan_path),
                f"BLOCKED: plan Target Outputs row {row_id} has {len(cells)} cells but header has {len(table.headers)} columns; row cells must match the header",
            )
        rows.append({field: cells[position] for position, field in enumerate(table.headers)})

    plan_context = PlanContext(
        path=plan_path,
        metadata=_plan_metadata(table.lines),
        items=tuple(rows),
    )
    if not rows:
        return "empty", plan_context, ""

    ids = [_item_id(item) for item in rows]
    if any(not task_id for task_id in ids):
        return "blocked", plan_context, "BLOCKED: plan contains an item without id"
    duplicates = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicates:
        return "blocked", plan_context, "BLOCKED: plan contains duplicate item ids: " + ", ".join(duplicates)

    known_ids = set(ids)
    for item in rows:
        unknown = [dep for dep in _expanded_depends(item.get("depends_on", "")) if dep not in known_ids]
        if unknown:
            return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} depends on unknown item {unknown[0]}"

    if scope_kind == "init":
        if _active_task_field(project_root, "stage").lower() != "init":
            return "blocked", plan_context, "BLOCKED: scan requires Init stage"
        contract_ids = []
        for item in rows:
            if _clean(item.get("phase", "")).lower() != "init":
                return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} phase is not Init"
            try:
                contract = load_task_contract(_contract_ref(item))
            except (ValueError, FileNotFoundError) as exc:
                return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} contract is not a valid Init task contract: {exc}"
            canonical = contract.get("_canonical_ref", "")
            if not canonical.startswith("init/"):
                return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} contract is not a valid Init task contract: {_contract_ref(item)}"
            contract_ids.append(_contract_id(item))
        if (
            contract_ids
            and all(contract_id in INIT_BOOTSTRAP_CONTRACT_IDS for contract_id in contract_ids)
            and all(_clean(item.get("output_files", "")) for item in rows)
        ):
            return "blocked", plan_context, "BLOCKED: bootstrap scan rows already have output_files; initial inspect_controller/sync_plan rows must not be prefilled"
    elif scope_kind == "feature":
        feature_id = _clean(plan_context.metadata.get("Feature ID", ""))
        if feature_id and feature_id != Path(scope_dir).name:
            return "blocked", plan_context, "BLOCKED: active_task/plan mismatch"
    elif scope_kind == "sync":
        for item in rows:
            try:
                contract = load_task_contract(_contract_ref(item))
            except (ValueError, FileNotFoundError) as exc:
                return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} contract is not a valid Sync task contract: {exc}"
            if not contract.get("_canonical_ref", "").startswith("sync/"):
                return "blocked", plan_context, f"BLOCKED: item {_item_id(item)} contract is not a valid Sync task contract: {_contract_ref(item)}"

    return "ready", plan_context, ""


def _bootstrap_route():
    contract = load_task_contract("init/plan.yaml")
    item = {
        "id": INIT_BOOTSTRAP_TASK_ID,
        "phase": "Init",
        "target": "workspace/_plan.md",
        "module": "workspace",
        "depends_on": "",
        "contract": "init/plan.yaml",
        "output_files": "",
    }
    return TaskRoute(item=item, contract=contract, workflow_ref=contract["workflow_ref"])


def _sync_plan_route():
    contract = load_task_contract("sync/plan.yaml")
    item = {
        "id": SYNC_BOOTSTRAP_TASK_ID,
        "phase": "Code",
        "target": "workspace/sync_plan.md",
        "depends_on": "",
        "contract": "sync/plan.yaml",
        "output_files": "",
    }
    return TaskRoute(item=item, contract=contract, workflow_ref=contract["workflow_ref"])


def _task_route_text(route, source):
    contract = route.contract
    item = route.item
    return "\n".join(
        [
            f"selected_item: {_item_id(item)}",
            f"selected_source: {source or 'auto ready'}",
            f"selected_phase: {_clean(item.get('phase', ''))}",
            f"selected_target: {_clean(item.get('target', ''))}",
            f"selected_contract: {_contract_ref(item)}",
            f"selected_canonical_contract: {contract.get('_canonical_ref', '')}",
        ]
    )


@dataclass(frozen=True)
class PreparedTask:
    """One deterministic Task Route and its Context Envelope."""

    status: str
    task_id: str = ""
    source: str = ""
    route: object = None
    envelope: object = None
    blocker: str = ""
    recommendation: object = None
    scope_kind: str = "feature"
    plan_path: object = None
    plan_signature: str = ""

    def render_markdown(self):
        if self.status == "READY" and self.envelope is not None:
            scope_option = " --scope sync" if self.scope_kind == "sync" else ""
            return "\n".join(
                [
                    f"READY: {self.task_id}",
                    "",
                    self.envelope.render().rstrip(),
                    "",
                    "# Completion Tool",
                    f"- task_id: {self.task_id}",
                    f"- fixed-output task: `shiki task complete <task_id>{scope_option}`",
                    f"- flexible-output task: `shiki task complete <task_id>{scope_option} --output <path>`",
                    f"- no change: `shiki task complete <task_id>{scope_option} --noop <reason>`",
                    "- CLI unavailable: replace `shiki` with `python -m shiki_cli`",
                ]
            ).rstrip() + "\n"
        if self.status == "DONE":
            return "DONE: plan complete\n"
        return (self.blocker or "BLOCKED: no ready task") + "\n"


def next_task(
    shiki_root,
    project_root,
    feature_dir,
    requested_item="",
    source="",
    task_route="",
    scope_kind="",
    plan_path=None,
    refresh_plan=False,
):
    """Select one task, enforce its Contract, and build its Context Envelope."""
    scope_kind = _scope_kind(feature_dir, scope_kind)
    if scope_kind == "init" and _active_task_field(project_root, "stage").lower() != "init":
        return PreparedTask(status="BLOCKED", blocker="BLOCKED: scan requires Init stage", scope_kind=scope_kind)
    plan_state, plan_context, blocker = _validate_scope_plan(
        project_root,
        feature_dir,
        scope_kind,
        plan_path=plan_path,
    )
    plan_signature = _plan_signature(plan_state, plan_context)
    if blocker:
        return PreparedTask(
            status="BLOCKED",
            blocker=blocker,
            scope_kind=scope_kind,
            plan_path=plan_context.path,
            plan_signature=plan_signature,
        )

    if scope_kind == "init" and plan_state in {"missing", "empty"}:
        route = _bootstrap_route()
        selected_request = ""
        selected_source = "Init plan bootstrap"
        decision = None
    elif scope_kind == "sync" and (plan_state in {"missing", "empty"} or refresh_plan):
        route = _sync_plan_route()
        selected_request = ""
        selected_source = "Sync plan"
        decision = None
    else:
        if plan_state in {"missing", "empty"}:
            return PreparedTask(
                status="BLOCKED",
                blocker="BLOCKED: plan required" if plan_state == "missing" else "BLOCKED: plan has no executable items",
                scope_kind=scope_kind,
                plan_path=plan_context.path,
                plan_signature=plan_signature,
            )
        items = plan_context.items
        item_ids = {_item_id(item) for item in items}
        active_next = _active_task_field(project_root, "next") if scope_kind == "feature" else ""
        if active_next.lower() in {"", "auto", "—", "-"} or active_next not in item_ids:
            active_next = ""
        requested = _clean(requested_item)
        if requested not in item_ids:
            requested = ""
        selected_request = active_next or requested
        selected_source = source or ("active_task.next" if active_next else ("user item" if selected_request else "auto ready"))
        if selected_request:
            decision = route_item_decision(feature_dir, selected_request, plan_context)
        else:
            decision = route_next_decision(feature_dir, plan_context)
        route = decision.route

    if route is None:
        items = plan_context.items
        if items and all(item_done(feature_dir, item, plan_context) for item in items):
            return PreparedTask(
                status="DONE",
                scope_kind=scope_kind,
                plan_path=plan_context.path,
                plan_signature=plan_signature,
            )
        return PreparedTask(
            status="BLOCKED",
            blocker=decision.blocker or "BLOCKED: no ready next item",
            recommendation=decision.recommendation,
            scope_kind=scope_kind,
            plan_path=plan_context.path,
            plan_signature=plan_signature,
        )

    selected_id = _item_id(route.item)
    if selected_request and selected_id != selected_request:
        selected_source = "required input producer"
    task_route = task_route or _task_route_text(route, selected_source)
    envelope = build_context_envelope(
        shiki_root=shiki_root,
        project_root=project_root,
        feature_dir=feature_dir,
        item=route.item,
        contract=route.contract,
        task_route=task_route,
        plan_context=plan_context,
    )
    if envelope.missing_required:
        return PreparedTask(
            status="BLOCKED",
            task_id=selected_id,
            source=selected_source,
            route=route,
            envelope=envelope,
            blocker="BLOCKED: missing required input: " + ", ".join(envelope.missing_required),
            recommendation=decision.recommendation if decision is not None else None,
            scope_kind=scope_kind,
            plan_path=plan_context.path,
            plan_signature=plan_signature,
        )
    return PreparedTask(
        status="READY",
        task_id=selected_id,
        source=selected_source,
        route=route,
        envelope=envelope,
        recommendation=decision.recommendation if decision is not None else None,
        scope_kind=scope_kind,
        plan_path=plan_context.path,
        plan_signature=plan_signature,
    )


@dataclass(frozen=True)
class TaskCompletion:
    """Result of a deterministic Plan completion update."""

    status: str
    task_id: str
    output_files: str = ""
    next_task: str = "auto"
    message: str = ""

    def render_markdown(self):
        summary = self.message or f"task {self.task_id} completed"
        lines = [f"{self.status}: {summary}"]
        if self.output_files:
            lines.append(f"- output_files: {self.output_files}")
        if self.status == "PASS":
            lines.append(f"- next: {self.next_task}")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class _PlanTable:
    lines: list
    headers: tuple
    row_start: int
    row_end: int
    trailing_newline: bool


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _plan_table(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    in_outputs = False
    header_index = None
    separator_index = None
    row_end = None
    headers = ()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^##\s+(Target Outputs|Target Artifacts)\s*$", stripped):
            in_outputs = True
            continue
        if in_outputs and re.match(r"^##\s+", stripped):
            row_end = index
            break
        if not in_outputs or not stripped.startswith("|"):
            if separator_index is not None and row_end is None:
                row_end = index
                break
            continue
        if header_index is None:
            header_index = index
            headers = tuple(_clean(cell) for cell in _table_cells(stripped))
            continue
        if separator_index is None:
            if not PLAN_SEPARATOR_RE.match(stripped):
                raise ValueError("Target Outputs is malformed")
            separator_index = index
            continue

    if header_index is None or separator_index is None:
        raise ValueError(f"plan Target Outputs table not found: {path}")
    if row_end is None:
        row_end = len(lines)
    return _PlanTable(
        lines=lines,
        headers=headers,
        row_start=separator_index + 1,
        row_end=row_end,
        trailing_newline=text.endswith("\n"),
    )


def _write_plan_table(path, table):
    text = "\n".join(table.lines)
    if table.trailing_newline:
        text += "\n"
    Path(path).write_text(text, encoding="utf-8")


def _render_plan_cell(field, value):
    clean = _clean(value)
    if not clean:
        return ""
    if "|" in clean or "\n" in clean:
        raise ValueError(f"plan {field} contains unsupported table characters")
    if field in {"target", "contract", "output_files"}:
        return f"`{clean}`"
    return clean


def _update_plan_item(path, task_id, updates):
    table = _plan_table(path)
    missing_fields = [field for field in updates if field not in table.headers]
    if missing_fields:
        raise ValueError("plan is missing fields: " + ", ".join(missing_fields))
    id_index = table.headers.index("id") if "id" in table.headers else -1
    matches = 0
    for index in range(table.row_start, table.row_end):
        stripped = table.lines[index].strip()
        if not stripped.startswith("|"):
            continue
        cells = _table_cells(stripped)
        if len(cells) != len(table.headers):
            raise ValueError(f"plan row has {len(cells)} cells; expected {len(table.headers)}")
        if id_index < 0 or _clean(cells[id_index]) != task_id:
            continue
        matches += 1
        for field, value in updates.items():
            cells[table.headers.index(field)] = _render_plan_cell(field, value)
        table.lines[index] = "| " + " | ".join(cells) + " |"
    if matches != 1:
        raise ValueError(f"plan task id must match exactly one row: {task_id}")
    _write_plan_table(path, table)


def _normalize_output_path(project_root, value):
    clean = _clean(value)
    if not clean:
        raise ValueError("output path must not be empty")
    if "," in clean:
        raise ValueError("output path must not contain a comma")
    status = clean.split(":", 1)[0].upper()
    if status in STOP_OUTPUT_STATUSES or status == "NOOP":
        raise ValueError(f"output path cannot use status {status}")
    path = Path(clean)
    if ".." in path.parts:
        raise ValueError(f"output path escapes project root: {path}")
    if path.is_absolute():
        try:
            clean = path.resolve().relative_to(Path(project_root).resolve()).as_posix()
        except ValueError:
            raise ValueError(f"output path escapes project root: {path}")
    return clean


def _declared_output_file(project_root, feature_dir, value):
    path = Path(value)
    if not path.is_absolute():
        if value.startswith("shiki_context/"):
            path = Path(project_root) / value
        elif value.startswith(("workspace/", "project/", "features/", "constitution/")):
            path = Path(project_root) / "shiki_context" / value
        elif value.startswith(("modules/", "tests/")):
            if Path(feature_dir).parent.name == "features":
                path = Path(feature_dir) / value
            else:
                path = Path(project_root) / "shiki_context" / value
        elif value in {"_plan.md", "index.md", "design_brief.md", "code_contract.md"}:
            path = Path(feature_dir) / value
        else:
            path = Path(project_root) / value
    try:
        path.resolve().relative_to(Path(project_root).resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def _fixed_output_ledger(feature_dir, item, contract):
    output = contract.get("output", {})
    pattern = _clean(output.get("path", "")) if isinstance(output, dict) else ""
    if not pattern:
        return ""
    target = _clean(item.get("target", ""))
    if "{target}" in pattern and target:
        return target
    feature = Path(feature_dir).name
    value = pattern.replace("{feature}", feature).replace("{target}", target)
    module_match = re.search(r"(?:^|/)modules/([^/]+)/", target)
    module = module_match.group(1) if module_match else ""
    value = value.replace("{module}", module)
    for prefix in [f"shiki_context/features/{feature}/", f"features/{feature}/"]:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def _next_task_id(feature_dir, plan_context):
    decision = route_next_decision(feature_dir, plan_context)
    return _item_id(decision.route.item) if decision.route is not None else "auto"


def update_active_task_next(project_root, task_id):
    """Update the developer-local next selector without creating another state file."""
    path = Path(project_root) / "shiki_context" / "workspace" / "active_task.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    replacement = f"- `next`: {task_id or 'auto'}"
    pattern = r"^\s*-\s+`next`:\s*.*$"
    if re.search(pattern, text, re.M):
        updated = re.sub(pattern, replacement, text, count=1, flags=re.M)
    else:
        lines = text.splitlines()
        insert_at = len(lines)
        for index, line in enumerate(lines):
            if re.match(r"^\s*-\s+(`feature`|\*\*.*Feature.*\*\*):", line, re.I):
                insert_at = index + 1
                break
        lines.insert(insert_at, replacement)
        updated = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    path.write_text(updated, encoding="utf-8")
    return True


def complete_task(
    project_root,
    feature_dir,
    task_id,
    output_files=(),
    noop_reason="",
    scope_kind="",
    plan_path=None,
):
    """Validate one Task result and update only its Plan completion fields."""
    scope_kind = _scope_kind(feature_dir, scope_kind)
    plan_path = Path(plan_path or (Path(feature_dir) / "_plan.md"))
    if task_id == INIT_BOOTSTRAP_TASK_ID and scope_kind == "init":
        plan_state, plan_context, blocker = _validate_scope_plan(
            project_root,
            feature_dir,
            scope_kind,
            plan_path=plan_path,
        )
        if blocker:
            return TaskCompletion("BLOCKED", task_id, message=_blocker_message(blocker))
        if plan_state != "ready" or not plan_context.items:
            return TaskCompletion("BLOCKED", task_id, message="Init plan was not created")
        prefilled = [_item_id(item) for item in plan_context.items if _clean(item.get("output_files", ""))]
        if prefilled:
            return TaskCompletion(
                "BLOCKED",
                task_id,
                message="initial Init plan rows must keep output_files empty: " + ", ".join(prefilled),
            )
        return TaskCompletion(
            "PASS",
            task_id,
            output_files="workspace/_plan.md",
            next_task=_next_task_id(feature_dir, plan_context),
            message="Init plan created",
        )

    if task_id == SYNC_BOOTSTRAP_TASK_ID and scope_kind == "sync":
        plan_state, plan_context, blocker = _validate_scope_plan(
            project_root,
            feature_dir,
            scope_kind,
            plan_path=plan_path,
        )
        if blocker:
            return TaskCompletion("BLOCKED", task_id, message=_blocker_message(blocker))
        if plan_state != "ready" or not plan_context.items:
            return TaskCompletion("BLOCKED", task_id, message="Sync plan was not created")
        return TaskCompletion(
            "PASS",
            task_id,
            output_files="workspace/sync_plan.md",
            next_task=_next_task_id(feature_dir, plan_context),
            message="Sync plan created",
        )

    plan_state, plan_context, blocker = _validate_scope_plan(
        project_root,
        feature_dir,
        scope_kind,
        plan_path=plan_path,
    )
    if blocker:
        return TaskCompletion("BLOCKED", task_id, message=_blocker_message(blocker))
    if plan_state != "ready":
        return TaskCompletion("BLOCKED", task_id, message="plan has no executable items")
    item = _plan_item(plan_context.items, task_id)
    if item is None:
        return TaskCompletion("BLOCKED", task_id, message="task is no longer a unique Plan item")

    if item_done(feature_dir, item, plan_context):
        next_task = _next_task_id(feature_dir, plan_context)
        if scope_kind == "feature":
            update_active_task_next(project_root, next_task)
        return TaskCompletion(
            "PASS",
            task_id,
            output_files=_clean(item.get("output_files", "")),
            next_task=next_task,
            message=f"task {task_id} was already complete",
        )

    decision = route_item_decision(feature_dir, task_id, plan_context)
    if decision.route is None or _item_id(decision.route.item) != task_id:
        return TaskCompletion(
            "BLOCKED",
            task_id,
            message=decision.blocker or "task is no longer the selected ready item",
        )

    if noop_reason and output_files:
        return TaskCompletion("BLOCKED", task_id, message="use either output_files or noop_reason")
    if noop_reason:
        reason = _clean(noop_reason)
        if not reason:
            return TaskCompletion("BLOCKED", task_id, message="NOOP requires a reason")
        ledger = f"NOOP: {reason}"
    else:
        contract = decision.route.contract
        fixed = _fixed_output_ledger(feature_dir, item, contract)
        values = []
        if fixed:
            fixed_path = resolve_artifact_path(
                project_root,
                feature_dir,
                item,
                contract["output"]["path"],
                plan_metadata=plan_context.metadata,
            )
            if fixed_path is None or not expand_artifact_path(fixed_path):
                return TaskCompletion("BLOCKED", task_id, message=f"required output does not exist: {fixed_path}")
            values.append(fixed)
        try:
            values.extend(_normalize_output_path(project_root, value) for value in output_files)
        except ValueError as exc:
            return TaskCompletion("BLOCKED", task_id, message=str(exc))
        values = list(dict.fromkeys(value for value in values if value))
        if not values:
            return TaskCompletion(
                "BLOCKED",
                task_id,
                message="flexible-output task requires --output or --noop",
            )
        missing = [value for value in values if _declared_output_file(project_root, feature_dir, value) is None]
        if missing:
            return TaskCompletion("BLOCKED", task_id, message=f"declared output is not a current file: {missing[0]}")
        ledger = ", ".join(values)

    candidate = dict(item)
    candidate["output_files"] = ledger
    if not item_done(feature_dir, candidate, plan_context):
        return TaskCompletion("BLOCKED", task_id, message="declared output_files are not current files")

    try:
        _update_plan_item(plan_path, task_id, {"output_files": ledger})
    except ValueError as exc:
        return TaskCompletion("BLOCKED", task_id, message=str(exc))

    next_state, next_context, blocker = _validate_scope_plan(
        project_root,
        feature_dir,
        scope_kind,
        plan_path=plan_path,
    )
    if blocker or next_state != "ready":
        next_task = "auto"
    else:
        next_task = _next_task_id(feature_dir, next_context)
    if scope_kind == "feature":
        update_active_task_next(project_root, next_task)
    return TaskCompletion("PASS", task_id, ledger, next_task)


def skip_optional_init_flows(project_root, scope_dir):
    """Mark consecutive ready legacy Init Flow rows as skipped by V4 scan policy."""
    skipped = []
    while True:
        plan_state, plan_context, blocker = _validate_scope_plan(project_root, scope_dir, "init")
        if blocker:
            return tuple(skipped), blocker
        if plan_state != "ready":
            return tuple(skipped), ""
        decision = route_next_decision(scope_dir, plan_context)
        if decision.route is None:
            return tuple(skipped), decision.blocker
        route = decision.route
        if route.contract.get("_canonical_ref") != "init/flow.yaml":
            return tuple(skipped), ""
        task_id = _item_id(route.item)
        completion = complete_task(
            project_root,
            scope_dir,
            task_id,
            noop_reason="optional flow skipped by V4 scan",
            scope_kind="init",
        )
        if completion.status != "PASS":
            return tuple(skipped), "BLOCKED: " + completion.message
        skipped.append(task_id)


@dataclass(frozen=True)
class PlanItemsUpdate:
    """Result of validated Plan row additions."""

    status: str
    added: tuple = ()
    skipped: tuple = ()
    message: str = ""

    def render_markdown(self):
        summary = self.message or f"added {len(self.added)} Plan item(s)"
        lines = [f"{self.status}: {summary}"]
        if self.added:
            lines.append("- added: " + ", ".join(self.added))
        if self.skipped:
            lines.append("- skipped: " + ", ".join(self.skipped))
        return "\n".join(lines) + "\n"


def _expanded_depends(value):
    result = []
    for raw in str(value or "").split(","):
        dep = _clean(raw)
        if not dep or dep in {"—", "-"}:
            continue
        match = re.match(r"^([A-Za-z]+)(\d+)-\1?(\d+)$", dep)
        if match:
            prefix, start, end = match.groups()
            result.extend(f"{prefix}{index}" for index in range(int(start), int(end) + 1))
        else:
            result.append(dep)
    return result


def plan_add_items(feature_dir, parent_task_id, new_items):
    """Add validated Canonical Plan rows without letting an Agent rewrite the table."""
    plan_path = Path(feature_dir) / "_plan.md"
    table = _plan_table(plan_path)
    missing_headers = [field for field in PLAN_FIELDS if field not in table.headers]
    if missing_headers:
        return PlanItemsUpdate("BLOCKED", message="plan is missing fields: " + ", ".join(missing_headers))
    existing = []
    for index in range(table.row_start, table.row_end):
        stripped = table.lines[index].strip()
        if not stripped.startswith("|"):
            continue
        cells = _table_cells(stripped)
        if len(cells) != len(table.headers):
            return PlanItemsUpdate("BLOCKED", message="plan row cells must match the header")
        existing.append({field: cells[position] for position, field in enumerate(table.headers)})
    if _plan_item(existing, parent_task_id) is None:
        return PlanItemsUpdate("BLOCKED", message="parent task is not a unique Plan item")

    existing_ids = {_item_id(item) for item in existing}
    existing_keys = {}
    try:
        for item in existing:
            canonical_ref = load_task_contract(_contract_ref(item))["_canonical_ref"]
            existing_keys[(canonical_ref, _clean(item.get("target", "")))] = _item_id(item)
    except (ValueError, FileNotFoundError) as exc:
        return PlanItemsUpdate("BLOCKED", message=f"existing Plan contract is invalid: {exc}")
    incoming_ids = {_clean(item.get("id", "")) for item in new_items}
    all_ids = existing_ids | incoming_ids
    normalized = []
    added = []
    skipped = []

    for raw_item in new_items:
        item = {field: _clean(raw_item.get(field, "")) for field in table.headers}
        task_id = item.get("id", "")
        if not task_id or not item.get("phase") or not item.get("target") or not item.get("contract"):
            return PlanItemsUpdate("BLOCKED", message="new Plan item requires id, phase, target and contract")
        if item.get("output_files"):
            return PlanItemsUpdate("BLOCKED", message=f"new Plan item {task_id} must start incomplete")
        try:
            contract = load_task_contract(item["contract"])
            item["contract"] = contract["_canonical_ref"]
            _target_path(feature_dir, item.get("target", ""))
        except (ValueError, FileNotFoundError) as exc:
            return PlanItemsUpdate("BLOCKED", message=str(exc))

        key = (item["contract"], item.get("target", ""))
        if key in existing_keys:
            if existing_keys[key] != task_id:
                return PlanItemsUpdate(
                    "BLOCKED",
                    message=f"contract + target already belongs to Plan item {existing_keys[key]}",
                )
            skipped.append(task_id)
            continue
        if task_id in existing_ids or any(candidate.get("id") == task_id for candidate in normalized):
            return PlanItemsUpdate("BLOCKED", message=f"duplicate Plan item id: {task_id}")
        unknown_dependencies = [dep for dep in _expanded_depends(item.get("depends_on", "")) if dep not in all_ids]
        if unknown_dependencies:
            return PlanItemsUpdate(
                "BLOCKED",
                message=f"Plan item {task_id} depends on unknown item {unknown_dependencies[0]}",
            )
        normalized.append(item)
        added.append(task_id)
        existing_keys[key] = task_id

    if not normalized:
        return PlanItemsUpdate("PASS", added=(), skipped=tuple(skipped), message="Plan already contains the requested items")

    row_lines = []
    try:
        for item in normalized:
            row_lines.append(
                "| " + " | ".join(_render_plan_cell(field, item.get(field, "")) for field in table.headers) + " |"
            )
    except ValueError as exc:
        return PlanItemsUpdate("BLOCKED", message=str(exc))
    table.lines[table.row_end:table.row_end] = row_lines
    _write_plan_table(plan_path, table)
    return PlanItemsUpdate("PASS", added=tuple(added), skipped=tuple(skipped))
