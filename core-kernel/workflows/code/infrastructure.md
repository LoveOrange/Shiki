# Infrastructure Code

> Role: Coder. Implement persistence and ACL infrastructure from current L2 AS-IS specs only.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/index.md`
- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/persistence.md`
- `features/{feature}/modules/{module}/designs/acl.md` when present
- target source and direct dependencies
- tech contracts: persistence, ACL, and exception

## Steps

1. Confirm model and persistence specs exist; ACL work also requires an ACL spec. Return `BLOCKED` when required specs are missing.
2. Compare current source to L2 specs and list table, Repository, Converter, and Support differences before editing.
3. Generate or update PO classes in `infrastructure/[module]/persistence/po/` with `PO` suffixes.
4. Use table names with the `[module]_` prefix.
5. Flatten VO fields into columns.
6. Generate Entity-to-PO converters and RepositoryImpl classes.
7. Generate SupportImpl classes for declared Support interfaces.
8. Translate external exceptions into AppException with declared error codes.
9. Update the matching plan item `output_files`.

## Verification

1. PO table names have the module prefix.
2. Support interfaces expose no external DTOs.
3. External exceptions are translated.
4. No direct low-level calls bypass Repository or Support contracts.
