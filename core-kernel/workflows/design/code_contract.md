# Generate Implementation Slice

> Role: Architect. Extract a temporary implementation slice from L2 AS-IS specs for the current Code task. The slice is not a long-lived fact source.


## Steps

1. Confirm all required design files exist.
2. Run the Design Contract Reuse Gate for implementation-slice scope.
3. If a leaf spec `§0 Baseline Delta` contains `reuse`, load the referenced baseline snippet and record it in `Source Specs`.
4. Extract facts into `code_contract.md`: Entities, DTOs, Interfaces, State Transitions, Error Codes, Non-functional Rules.
5. Add `[ ]` confirmation markers for each implementable fact.
6. Set `Contract Version: v1` unless a version is already required by the plan.
7. Do not add design facts or implementation details not present in L2 specs or explicitly reused baseline refs.

## Output

- `features/{feature}/code_contract.md`

## Verification

1. Sections 1-6 are present.
2. Names match upstream design files.
3. Source Specs are recorded.
4. Confirmation cells start unchecked.
5. Contract Version is set.
6. Every implementation fact traces to an upstream L2 spec or explicit reuse ref.
