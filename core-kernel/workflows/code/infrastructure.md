# Infrastructure Code

> Role: Coder. Implement persistence and ACL infrastructure declared by `code_contract.md` only.

## Load

- `features/{feature}/code_contract.md`
- `features/{feature}/_plan.md`
- target source and direct dependencies
- tech contracts: persistence, ACL, and exception

## Steps

1. Confirm `code_contract.md` exists and has a concrete Contract Version.
2. Generate PO classes in `infrastructure/[module]/persistence/po/` with `PO` suffixes.
3. Use table names with the `[module]_` prefix.
4. Flatten VO fields into columns.
5. Generate Entity-to-PO converters and RepositoryImpl classes.
6. Generate SupportImpl classes for declared Support interfaces.
7. Translate external exceptions into AppException with declared error codes.
8. Update the matching plan item output_files.

## Verification

1. PO table names have the module prefix.
2. Support interfaces expose no external DTOs.
3. External exceptions are translated.
4. No direct low-level calls bypass Repository or Support contracts.
