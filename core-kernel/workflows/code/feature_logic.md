# Feature Logic

> Role: Coder. Implement application/domain behavior declared by `code_contract.md` only.

## Load

- `features/{feature}/code_contract.md`
- `features/{feature}/_plan.md`
- target source and direct call-chain source
- tech contracts: layering and exception

## Steps

1. Confirm `code_contract.md` exists and has a concrete Contract Version.
2. Read Interfaces, State Transitions, Error Codes, and Non-functional Rules.
3. Implement AppService and DomainService methods with exact signatures.
4. Implement state transitions and throw declared AppException/ErrorCode values.
5. Apply declared transaction, idempotency, and concurrency rules.
6. Inject domain/infrastructure interfaces through constructors.
7. Update the matching plan item output_files.

## Verification

1. Signatures match the contract.
2. ErrorCode usage matches the contract.
3. No undeclared Repository or Support methods are invented.
4. Application layer does not directly depend on infrastructure implementations.
