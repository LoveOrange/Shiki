# Adapter Code

> Role: Coder. Implement transport adapters from current L2 AS-IS specs only.


## Steps

1. Confirm component and entrance specs exist and the entry route is codable; otherwise return `BLOCKED`.
2. Compare current source to L2 specs and list URL, DTO, AppService call, and branch differences before editing.
3. Generate or update REST controllers, message listeners, or jobs declared by entrance/component specs.
4. Use DTOs for adapter input and output.
5. Call AppService only from adapters.
6. Keep business logic out of adapters.
7. Update the matching plan item `output_files`.

## Verification

1. Adapter input/output types are DTOs, not Entities.
2. Adapters depend only on AppService boundaries.
3. Endpoints match entrance specs.
4. No business logic is implemented in adapters.
