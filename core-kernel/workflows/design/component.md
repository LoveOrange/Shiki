# Component Design

> Role: Architect. Produce layered component design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/persistence.md`
- `features/{feature}/modules/{module}/designs/acl.md`
- baseline `modules/{module}/designs/component.md` when present and read-only
- tech contracts: layering and naming

## Steps

1. Confirm model, persistence, and ACL designs exist.
2. Fill `_component_template.md`: Baseline Delta, component diagram, inventory, and interface contracts.
3. For feature overlays, compare baseline component when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
4. Keep method signatures aligned with model and ACL specs.
5. Reference Support interfaces from ACL instead of duplicating them.
6. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/component.md`

## Verification

1. Output file exists.
2. Selected layers are represented.
3. Method signatures match upstream specs.
4. Support contracts are referenced consistently.
5. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
