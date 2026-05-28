# Interface Skeletons

> Role: Coder. Generate interfaces and DTO skeletons from current L2 AS-IS specs only.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/index.md`
- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/component.md`
- existing source and same-layer examples
- tech contracts: naming and layering

## Steps

1. Confirm model and component specs exist and contain codable interfaces, DTOs, and method signatures.
2. Read DTOs and interfaces from component spec; read model spec to keep Entity/VO boundaries correct.
3. Compare current source to L2 specs and list signature, field, and path differences before editing.
4. Generate or update AppService, DomainService, Repository, and Support interfaces as declared.
5. Generate DTO classes with the `DTO` suffix.
6. Keep method names, parameters, and return values exactly aligned with current specs.
7. Update the matching plan item `output_files`.

## Verification

1. Method signatures match the current component spec.
2. DTO fields match the current component spec.
3. No implementation classes are generated.
4. Paths match selected layering rules.
