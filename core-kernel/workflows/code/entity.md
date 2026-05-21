# Entity Code

> Role: Coder. Translate `code_contract.md` into domain model code only. Return BLOCKED when the contract is missing or unversioned.

## Load

- `features/{feature}/code_contract.md`
- `features/{feature}/_plan.md`
- target source files and direct dependencies
- tech contracts: naming and layering

## Steps

1. Confirm `code_contract.md` exists and has a concrete Contract Version.
2. Read Entities and State Transitions.
3. Generate Entity classes without suffixes and VO classes with `VO` suffixes.
4. Keep Entity classes free of persistence, serialization, and framework annotations.
5. Generate state enums only from declared states.
6. Place domain model code under `domain/[module]/model/`.
7. Update the matching plan item output_files.

## Verification

1. Class and field names match the contract.
2. Entity classes have no framework annotations.
3. Paths match selected layering rules.
4. No undeclared fields or states are added.
