# Adapter Code

> Role: Coder. Implement transport adapters from `code_contract.md` only.

## Load

- `features/{feature}/code_contract.md`
- `features/{feature}/_plan.md`
- target source
- tech contracts: naming and layering

## Steps

1. Confirm `code_contract.md` exists and has a concrete Contract Version.
2. Generate REST controllers, message listeners, or jobs declared by the contract.
3. Use DTOs for adapter input and output.
4. Call AppService only from adapters.
5. Keep business logic out of adapters.
6. Update the matching plan item output_files.

## Verification

1. Adapter input/output types are DTOs, not Entities.
2. Adapters depend only on AppService boundaries.
3. Endpoints match code contract or entrance spec.
4. No business logic is implemented in adapters.
