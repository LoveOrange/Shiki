# Component Design

> Role: Architect. Produce layered component design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/persistence.md`
- `features/{feature}/modules/{module}/designs/acl.md`
- tech contracts: layering and naming

## Steps

1. Confirm model, persistence, and ACL designs exist.
2. Fill `_component_template.md`: component diagram, inventory, and interface contracts.
3. Keep method signatures aligned with model and ACL specs.
4. Reference Support interfaces from ACL instead of duplicating them.
5. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/component.md`

## Verification

1. Output file exists.
2. Selected layers are represented.
3. Method signatures match upstream specs.
4. Support contracts are referenced consistently.
