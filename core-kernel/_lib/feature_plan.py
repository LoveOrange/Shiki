"""Feature plan rendering and parsing helpers."""

import re
from datetime import date

from .markdown import extract_section, metadata_value, parse_table, read_text


BOOTSTRAP_CONTRACT = "core-kernel/runtime/task_contracts/design/design_init.yaml"
MODEL_CONTRACT = "core-kernel/runtime/task_contracts/design/model.yaml"
PERSISTENCE_CONTRACT = "core-kernel/runtime/task_contracts/design/persistence.yaml"
ACL_CONTRACT = "core-kernel/runtime/task_contracts/design/acl.yaml"
COMPONENT_CONTRACT = "core-kernel/runtime/task_contracts/design/component.yaml"
ENTRANCE_SPEC_CONTRACT = "core-kernel/runtime/task_contracts/design/entrance_spec.yaml"
FLOW_CONTRACT = "core-kernel/runtime/task_contracts/design/flow.yaml"
CODE_CONTRACT_CONTRACT = "core-kernel/runtime/task_contracts/design/code_contract.yaml"
CODE_ENTITY_CONTRACT = "core-kernel/runtime/task_contracts/code/entity.yaml"
CODE_INTERFACE_CONTRACT = "core-kernel/runtime/task_contracts/code/interface_skeletons.yaml"
CODE_FEATURE_CONTRACT = "core-kernel/runtime/task_contracts/code/feature_logic.yaml"
CODE_INFRA_CONTRACT = "core-kernel/runtime/task_contracts/code/infrastructure.yaml"
CODE_ADAPTER_CONTRACT = "core-kernel/runtime/task_contracts/code/adapter.yaml"
MERGE_CONTRACT = "core-kernel/runtime/task_contracts/merge/feature_merge.yaml"


def today_iso():
    """Return today's date in ISO format."""
    return date.today().isoformat()


def detect_base_module(brief_text, feature_id):
    """Detect the base module from design_brief.md, with a stable fallback."""
    match = re.search(r"\*\*Module\*\*:\s*([^\n*]+)", brief_text)
    if match:
        value = match.group(1).strip()
        if value and value not in {"[optional; design_init may infer it]", "[___]", "N/A", "-", "[TBD]"}:
            return value
    normalized = re.sub(r"[^a-z0-9]+", "_", feature_id.lower()).strip("_")
    return normalized or "feature"


def _markdown_table(headers, rows):
    header_line = "| " + " | ".join(headers) + " |"
    separator = "|" + "|".join(":---" for _ in headers) + "|"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator] + body)


def _clean_cell(value):
    return value.strip().strip("`").strip()


def _meaningful_bullets(section_text):
    bullets = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        value = line[2:].strip()
        if not value or value.startswith("["):
            continue
        bullets.append(value)
    return bullets


def render_bootstrap_plan(feature_id, created_on):
    """Render the initial bootstrap plan created by new_feature.py."""
    rows = [[
        "B1",
        "Design",
        "design_init",
        "`_plan.md`",
        "-",
        f"`{BOOTSTRAP_CONTRACT}`",
        "",
    ]]
    table = _markdown_table(
        ["id", "phase", "kind", "target", "depends_on", "contract", "output_files"],
        rows,
    )
    return "\n".join(
        [
            f"# Feature Plan: {feature_id}",
            "",
            "> Bootstrap plan created by `new_feature.py`.",
            "> design_init must expand it into the full task list.",
            "",
            "## Meta",
            "",
            f"- **Feature ID**: {feature_id}",
            "- **Base Module**: [TBD]",
            "- **Contract Version**: [TBD]",
            f"- **Created**: {created_on}",
            "",
            "## Target Artifacts",
            "",
            table,
            "",
            "> `contract` points to YAML files under `core-kernel/runtime/task_contracts/`.",
        ]
    )


def render_feature_index(feature_id, items):
    """Render the feature index from the current plan items."""
    generated_rows = []
    for item in items:
        phase = _clean_cell(item.get("phase", ""))
        kind = _clean_cell(item.get("kind", ""))
        target = _clean_cell(item.get("target", ""))
        item_id = _clean_cell(item.get("id", ""))
        if phase != "Design":
            continue
        if kind in {"design_init", "code_contract"}:
            continue
        if target in {"", "-", "baseline", "module baseline"}:
            continue
        artifact_id = target.rsplit(".", 1)[0].replace("/", ".")
        generated_rows.append([f"`{kind}`", f"`{artifact_id}`", f"`{target}`", item_id])

    generated_table = _markdown_table(
        ["kind", "id", "path", "source item"],
        generated_rows or [["*(design_init appends here)*", "", "", ""]],
    )
    return "\n".join(
        [
            f"# Feature Spec Index: {feature_id}",
            "",
            "> Agent/runtime routing entry. It records feature artifacts and load paths only.",
            "",
            "## Scope Files",
            "",
            "| file | role |",
            "| :--- | :--- |",
            "| `README.md` | human entry point |",
            "| `index.md` | context routing |",
            "| `_plan.md` | feature task ledger |",
            "",
            "## Feature Spec Artifacts",
            "",
            "| kind | id | path | load when |",
            "| :--- | :--- | :--- | :--- |",
            "| `design_input` | `design_brief` | `design_brief.md` | requirement and design initialization |",
            "| `contract_spec` | `code_contract` | `code_contract.md` | code and test work |",
            "| `test_spec` | `test_cases` | `tests/test_cases.md` | test design and acceptance coverage |",
            "",
            "## Generated Spec Artifacts",
            "",
            "After design_init, record only leaf specs declared by `_plan.md`.",
            "Feature module specs use overlay paths aligned with baseline `modules/{module}/...`.",
            "",
            generated_table,
            "",
            "## Loading Protocol",
            "",
            "1. Read `_plan.md` first to identify the current item.",
            "2. Read this `index.md` only when the item needs feature leaf-spec routing.",
            "3. Load direct dependencies from the item's `target` and `depends_on` fields.",
            "4. If this index conflicts with a leaf spec, trust the leaf spec and fix the index.",
            "",
        ]
    )


def infer_scope_from_brief(brief_text):
    """Infer minimal plan shape from the design brief."""
    entrance_section = extract_section(brief_text, "External Entrances and Capacity")
    boundary_section = extract_section(brief_text, "Boundaries and Dependencies")
    entrance_bullets = _meaningful_bullets(entrance_section)
    boundary_bullets = _meaningful_bullets(boundary_section)
    has_entrance = any(
        keyword in bullet.lower()
        for bullet in entrance_bullets
        for keyword in ["add", "new", "change", "yes"]
    )
    needs_acl = any(bullet.strip().lower() not in {"n/a", "none", "no"} for bullet in boundary_bullets)
    return {
        "has_entrance": has_entrance,
        "needs_acl": needs_acl,
    }


def render_full_plan(feature_id, base_module, created_on, has_entrance, needs_acl):
    """Render the full feature plan produced by design_init."""
    module_root = f"modules/{base_module}"
    model_target = f"`{module_root}/designs/model.md`"
    persistence_target = f"`{module_root}/designs/persistence.md`"
    acl_target = f"`{module_root}/designs/acl.md`"
    component_target = f"`{module_root}/designs/component.md`"
    entrance_target = f"`{module_root}/entrances/main.md`"
    flow_target = f"`{module_root}/flows/main.md`"
    rows = [
        ["D1", "Design", "model", model_target, "-", f"`{MODEL_CONTRACT}`", ""],
        ["D2", "Design", "persistence", persistence_target, "D1", f"`{PERSISTENCE_CONTRACT}`", ""],
    ]
    if needs_acl:
        rows.append(["D3", "Design", "acl", acl_target, "D1", f"`{ACL_CONTRACT}`", ""])
        component_depends = "D1,D2,D3"
        flow_depends = "D1,D2,D3,D4"
        cp_depends = "D1-D6" if has_entrance else "D1-D4,D6"
    else:
        component_depends = "D1,D2"
        flow_depends = "D1,D2,D4"
        cp_depends = "D1-D4,D6" if has_entrance else "D1,D2,D4,D6"

    rows.append(["D4", "Design", "component", component_target, component_depends, f"`{COMPONENT_CONTRACT}`", ""])
    if has_entrance:
        rows.append(["D5", "Design", "entrance_spec", entrance_target, "D1", f"`{ENTRANCE_SPEC_CONTRACT}`", ""])
    rows.append(["D6", "Design", "flow", flow_target, flow_depends, f"`{FLOW_CONTRACT}`", ""])
    rows.extend(
        [
            ["CP", "Design", "code_contract", "`code_contract.md`", cp_depends, f"`{CODE_CONTRACT_CONTRACT}`", ""],
            ["C1", "Code", "entity", "-", "CP", f"`{CODE_ENTITY_CONTRACT}`", ""],
            ["C2", "Code", "interface_skeletons", "-", "C1", f"`{CODE_INTERFACE_CONTRACT}`", ""],
            ["C3", "Code", "feature_logic", "-", "C2", f"`{CODE_FEATURE_CONTRACT}`", ""],
            ["C4", "Code", "infrastructure", "-", "C3", f"`{CODE_INFRA_CONTRACT}`", ""],
            ["C5", "Code", "adapter", "-", "C4", f"`{CODE_ADAPTER_CONTRACT}`", ""],
            ["M1", "Merge", "feature_merge", "baseline", "C5", f"`{MERGE_CONTRACT}`", ""],
        ]
    )

    table = _markdown_table(
        ["id", "phase", "kind", "target", "depends_on", "contract", "output_files"],
        rows,
    )
    return "\n".join(
        [
            f"# Feature Plan: {feature_id}",
            "",
            "> Expanded by design_init from the bootstrap plan.",
            "",
            "## Meta",
            "",
            f"- **Feature ID**: {feature_id}",
            f"- **Base Module**: {base_module}",
            "- **Contract Version**: [TBD]",
            f"- **Created**: {created_on}",
            "",
            "## Target Artifacts",
            "",
            table,
            "",
            "> `contract` points to YAML files under `core-kernel/runtime/task_contracts/`.",
            "> Delete rows that do not apply to the feature.",
        ]
    )


def expand_plan_from_brief(feature_dir, feature_id):
    """Expand a bootstrap plan into the full task list based on design_brief.md."""
    brief_path = feature_dir / "design_brief.md"
    brief_text = read_text(brief_path)
    scope = infer_scope_from_brief(brief_text)
    plan_path = feature_dir / "_plan.md"
    metadata = {}
    if plan_path.exists():
        metadata, _ = parse_plan(plan_path)
    created_on = metadata.get("Created") or today_iso()
    base_module = detect_base_module(brief_text, feature_id)
    plan = render_full_plan(
        feature_id=feature_id,
        base_module=base_module,
        created_on=created_on,
        has_entrance=scope["has_entrance"],
        needs_acl=scope["needs_acl"],
    )
    plan_path.write_text(plan, encoding="utf-8")
    _, items = parse_plan(plan_path)
    (feature_dir / "index.md").write_text(render_feature_index(feature_id, items), encoding="utf-8")
    return plan_path


def parse_plan(path):
    """Parse a feature plan markdown file."""
    text = read_text(path)
    metadata = {
        "Feature ID": metadata_value(text, "Feature ID"),
        "Base Module": metadata_value(text, "Base Module"),
        "Contract Version": metadata_value(text, "Contract Version"),
        "Created": metadata_value(text, "Created"),
    }
    items = parse_table(extract_section(text, "Target Artifacts"))
    return metadata, items


def is_bootstrap_plan(items):
    """Return True when a plan still contains only the bootstrap row."""
    return len(items) == 1 and items[0].get("kind") == "design_init"
