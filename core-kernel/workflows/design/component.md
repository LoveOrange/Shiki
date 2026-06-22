# Component Design

> Role: Architect. Produce layered component design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/persistence.md`
- `features/{feature}/modules/{module}/designs/acl.md`
- baseline `modules/{module}/designs/component.md` when present and read-only
- `core-kernel/runtime/design_contract.md`
- tech contracts: layering and naming

## Steps

1. Confirm model, persistence, and ACL designs exist.
2. Run the Design Contract Reuse Gate for component scope: list checked baseline/source components, services, repositories, supports, and adapters.
3. Fill `_component_template.md`: Baseline Delta, Reuse Decision Gate, component diagram, inventory, and interface contracts.
4. For feature overlays, compare baseline component when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
5. Keep method signatures aligned with model and ACL specs.
6. Reference Support interfaces from ACL instead of duplicating them.
7. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/component.md`

## Verification

1. Output file exists.
2. Selected layers are represented.
3. Method signatures match upstream specs.
4. Support contracts are referenced consistently.
5. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
6. Reuse Decision Gate records checked candidates and add justification.
