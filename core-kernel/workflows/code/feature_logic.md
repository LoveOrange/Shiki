# Feature Logic

> Role: Coder. Implement application/domain behavior from current L2 AS-IS specs only.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/index.md`
- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/component.md`
- `features/{feature}/modules/{module}/designs/acl.md` when present
- `features/{feature}/modules/{module}/flows/*.md`
- target source and direct call-chain source
- tech contracts: layering and exception

## Steps

1. Confirm model, component, and flow specs exist and map to target source; otherwise return `BLOCKED`.
2. Read interfaces, state transitions, error codes, non-functional rules, and ACL rules.
3. Compare current source to L2 specs and list signature, state, error-code, transaction, idempotency, and concurrency differences before editing.
4. Implement AppService and DomainService methods with exact signatures.
5. Implement state transitions from current AS-IS model and flow specs; failed preconditions throw declared AppException/ErrorCode values.
6. Apply declared transaction, idempotency, and concurrency rules.
7. Inject domain/infrastructure interfaces through constructors.
8. Update the matching plan item `output_files`.

## Verification

1. Signatures match the current component spec.
2. ErrorCode usage matches current model and flow specs.
3. No undeclared Repository or Support methods are invented.
4. Application layer does not directly depend on infrastructure implementations.
