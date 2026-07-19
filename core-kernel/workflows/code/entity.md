# Entity Code

> Role: Coder. Implement only what the current L2 AS-IS specs declare. Return BLOCKED when required leaf specs or target code context are missing.


## Steps

1. Confirm the model spec exists and maps to target source; otherwise return `BLOCKED`.
2. Extract entities, value objects, enums, fields, invariants, and states from the model spec.
3. Use flow specs only to confirm state triggers and business transitions.
4. Compare current source to L2 specs and list missing, stale, and conflicting facts before editing.
5. Generate or update Entity classes without suffixes and VO classes with `VO` suffixes.
6. Keep Entity classes free of persistence, serialization, and framework annotations.
7. Generate state enums only from declared states.
8. Update the matching plan item `output_files`.

## Verification

1. Class and field names match the current model spec.
2. Entity classes have no framework annotations.
3. Paths match selected layering rules.
4. No undeclared fields or states are added.
