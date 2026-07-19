"""Feature plan rendering and parsing helpers."""

import re
from datetime import date

from .markdown import extract_section, metadata_value, parse_table, read_text


BOOTSTRAP_CONTRACT = "design/design_init.yaml"
MODEL_CONTRACT = "design/model.yaml"
PERSISTENCE_CONTRACT = "design/persistence.yaml"
ACL_CONTRACT = "design/acl.yaml"
COMPONENT_CONTRACT = "design/component.yaml"
ENTRANCE_SPEC_CONTRACT = "design/entrance_spec.yaml"
CODE_ENTITY_CONTRACT = "code/entity.yaml"
CODE_INTERFACE_CONTRACT = "code/interface_skeletons.yaml"
CODE_FEATURE_CONTRACT = "code/feature_logic.yaml"
CODE_INFRA_CONTRACT = "code/infrastructure.yaml"
CODE_ADAPTER_CONTRACT = "code/adapter.yaml"
TEST_API_CASE_CONTRACT = "test/api_case_spec.yaml"
TEST_UNIT_CASE_CONTRACT = "test/unit_case_spec.yaml"
TEST_UNIT_CODE_CONTRACT = "test/unit_test_code.yaml"
TEST_API_CODE_CONTRACT = "test/api_integration_test_code.yaml"
TEST_RUN_CONTRACT = "test/run.yaml"
MERGE_CONTRACT = "merge/feature_merge.yaml"


def today_iso():
    """Return today's date in ISO format."""
    return date.today().isoformat()


def detect_base_module(brief_text, feature_id):
    """Detect the base module from design_brief.md, with a stable fallback."""
    match = re.search(r"\*\*Module\*\*:\s*([^\n*]+)", brief_text)
    if match:
        value = match.group(1).strip()
        if value and value not in {"[optional; design_init may infer it]", "[___]", "N/A", "—"}:
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


def _contract_ref(item):
    return _clean_cell(item.get("contract", ""))


def _contract_matches(item, suffix):
    return _contract_ref(item).endswith(suffix)


def _spec_level_for_target(target):
    if "/entrances/" in target or target.endswith("/designs/model.md"):
        return "L1"
    if (
        "/flows/" in target
        or target.endswith("/designs/persistence.md")
        or target.endswith("/designs/acl.md")
        or target.endswith("/designs/component.md")
        or target.endswith("/tests/test_cases.md")
    ):
        return "L2"
    return "L2"


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
        "`_plan.md`",
        "—",
        f"`{BOOTSTRAP_CONTRACT}`",
        "",
    ]]
    table = _markdown_table(
        ["id", "phase", "target", "depends_on", "contract", "output_files"],
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
            "- **Spec Revision**: AS-IS",
            f"- **Created**: {created_on}",
            "",
            "## Target Outputs",
            "",
            table,
            "",
            "> `contract` references YAML under `core-kernel/runtime/task_contracts/` with the common prefix omitted.",
        ]
    )


def render_feature_index(feature_id, items):
    """Render the feature index from the current plan items."""
    generated_rows = []
    for item in items:
        phase = _clean_cell(item.get("phase", ""))
        target = _clean_cell(item.get("target", ""))
        item_id = _clean_cell(item.get("id", ""))
        if phase != "Design":
            continue
        if _contract_matches(item, "design/design_init.yaml") or _contract_matches(item, "design/code_contract.yaml"):
            continue
        contract_ref = _contract_ref(item)
        if contract_ref.startswith("core-kernel/runtime/task_contracts/test/") or contract_ref.startswith("test/"):
            continue
        if target in {"", "—", "baseline", "module baseline"}:
            continue
        spec_id = target.rsplit(".", 1)[0].replace("/", ".")
        generated_rows.append([f"`{spec_id}`", _spec_level_for_target(target), f"`{target}`", item_id])

    generated_table = _markdown_table(
        ["id", "level", "path", "source item"],
        generated_rows or [["*(design_init appends here)*", "", "", ""]],
    )
    return "\n".join(
        [
            f"# Feature Spec Index: {feature_id}",
            "",
            "> Agent/runtime routing entry. It records feature spec files and load paths, not design content.",
            "",
            "## Scope Files",
            "",
            "| file | role |",
            "| :--- | :--- |",
            "| `README.md` | human entry point |",
            "| `index.md` | context routing |",
            "| `_plan.md` | feature task and output ledger |",
            "",
            "## Feature Spec Files",
            "",
            "| id | level | path | load when |",
            "| :--- | :--- | :--- | :--- |",
            "| `design_brief` | N/A | `design_brief.md` | design initialization and requirement correction |",
            "| `code_contract` | N/A | `code_contract.md` | optional Code Contract when direct specs exceed the context budget; not a durable spec |",
            "| `test_cases` | L2 | `tests/test_cases.md` | Test tasks, automated test code, and acceptance coverage |",
            "",
            "## Generated Spec Files",
            "",
            "After design initialization, record only leaf specs declared by `_plan.md` that exist or are confirmed outputs.",
            "Feature module specs use overlay paths relative to the current feature root.",
            "`modules/{module}/...` means `shiki_context/features/{feature}/modules/{module}/...`, not baseline `shiki_context/modules/{module}/...`.",
            "Each feature overlay leaf spec must record Baseline References in `§0 Feature Change`, mark `spec_change_state` as `add/modify/deprecate`, and remain a bounded overlay.",
            "",
            generated_table,
            "",
            "## Loading Protocol",
            "",
            "1. Read `_plan.md` first to identify the current item.",
            "2. Read this `index.md` only when the current item needs feature leaf-spec routing.",
            "3. Load direct dependencies from the current item's `target` and `depends_on` fields.",
            "4. Trust the index for level/routing and the leaf spec for content; fix the index or split the leaf when they conflict.",
            "",
        ]
    )


def infer_scope_from_brief(brief_text):
    """Infer minimal plan shape from the design brief."""
    entrance_section = extract_section(brief_text, "External Entrances and Capacity")
    boundary_section = extract_section(brief_text, "Boundaries and Dependencies")
    entrance_bullets = _meaningful_bullets(entrance_section)
    boundary_bullets = _meaningful_bullets(boundary_section)
    has_entrance = any("add" in bullet or "change" in bullet for bullet in entrance_bullets)
    needs_acl = any(bullet not in {"N/A", "none"} for bullet in boundary_bullets)
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
    rows = [
        ["D1", "Design", model_target, "—", f"`{MODEL_CONTRACT}`", ""],
        ["D2", "Design", persistence_target, "D1", f"`{PERSISTENCE_CONTRACT}`", ""],
    ]
    if needs_acl:
        rows.append(["D3", "Design", acl_target, "D1", f"`{ACL_CONTRACT}`", ""])
        component_depends = "D1,D2,D3"
        feature_logic_depends = "C2,D3"
        infrastructure_depends = "C1,C2,D2,D3"
    else:
        component_depends = "D1,D2"
        feature_logic_depends = "C2"
        infrastructure_depends = "C1,C2,D2"

    rows.append(["D4", "Design", component_target, component_depends, f"`{COMPONENT_CONTRACT}`", ""])
    if has_entrance:
        rows.append(["D5", "Design", entrance_target, "D1", f"`{ENTRANCE_SPEC_CONTRACT}`", ""])
        adapter_depends = "C2,D4,D5"
    else:
        adapter_depends = "C2,D4"
    if has_entrance:
        rows.append(["T1", "Design", "`tests/test_cases.md`", "D5", f"`{TEST_API_CASE_CONTRACT}`", ""])
    rows.extend(
        [
            ["C1", "Code", "—", "D1", f"`{CODE_ENTITY_CONTRACT}`", ""],
            ["C2", "Code", "—", "D1,D4", f"`{CODE_INTERFACE_CONTRACT}`", ""],
            ["C3", "Code", "—", feature_logic_depends, f"`{CODE_FEATURE_CONTRACT}`", ""],
            ["C4", "Code", "—", infrastructure_depends, f"`{CODE_INFRA_CONTRACT}`", ""],
            ["C5", "Code", "—", adapter_depends, f"`{CODE_ADAPTER_CONTRACT}`", ""],
            ["T2", "Code", "`tests/test_cases.md`", "C1,C2,C3,C4,C5", f"`{TEST_UNIT_CASE_CONTRACT}`", ""],
            ["T3", "Code", "—", "T2,C1,C2,C3,C4,C5", f"`{TEST_UNIT_CODE_CONTRACT}`", ""],
        ]
    )
    if has_entrance:
        rows.append(["T4", "Test", "—", "T1,C5", f"`{TEST_API_CODE_CONTRACT}`", ""])
        run_depends = "T3,T4"
    else:
        run_depends = "T3"
    rows.extend(
        [
            ["T5", "Test", "test evidence", run_depends, f"`{TEST_RUN_CONTRACT}`", ""],
            ["M1", "Merge", "baseline", "T5", f"`{MERGE_CONTRACT}`", ""],
        ]
    )

    table = _markdown_table(
        ["id", "phase", "target", "depends_on", "contract", "output_files"],
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
            "- **Spec Revision**: AS-IS",
            f"- **Created**: {created_on}",
            "",
            "## Target Outputs",
            "",
            "> `target` is relative to the current feature root; `modules/...` means feature overlay, not baseline `shiki_context/modules/...`.",
            "",
            table,
            "",
            "> `contract` points to YAML under `core-kernel/runtime/task_contracts/`.",
            "> Delete rows that do not apply.",
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
        "Spec Revision": metadata_value(text, "Spec Revision"),
        "Contract Version": metadata_value(text, "Contract Version"),
        "Created": metadata_value(text, "Created"),
    }
    legacy_heading = "Target " + "Arti" + "facts"
    section = extract_section(text, "Target Outputs") or extract_section(text, legacy_heading)
    items = parse_table(section)
    return metadata, items


def is_bootstrap_plan(items):
    """Return True when a plan still contains only the bootstrap row."""
    return len(items) == 1 and _contract_matches(items[0], "design/design_init.yaml")
