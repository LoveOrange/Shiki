# Interface Skeletons

> Role: Coder. Generate interfaces and DTO skeletons from `code_contract.md` only.

## Load

- `features/{feature}/code_contract.md`
- `features/{feature}/_plan.md`
- existing source and same-layer examples
- tech contracts: naming and layering

## Steps

1. Confirm `code_contract.md` exists and has a concrete Contract Version.
2. Read DTOs and Interfaces.
3. Generate AppService, DomainService, Repository, and Support interfaces as declared.
4. Generate DTO classes with the `DTO` suffix.
5. Keep method names, parameters, and return values exactly aligned with the contract.
6. Update the matching plan item output_files.

## Verification

1. Method signatures match the contract.
2. DTO fields match the contract.
3. No implementation classes are generated.
4. Paths match selected layering rules.
