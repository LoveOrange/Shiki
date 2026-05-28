# Feature Merge

> Role: Reviewer. Merge accepted feature overlay specs into baseline after verification.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/index.md`
- `features/{feature}/modules/{module}/...`
- `features/{feature}/tests/test_cases.md` when present
- `shiki_context/modules/{module}/index.md`

## Steps

1. Confirm every required plan item has output_files.
2. Confirm no output_files entry is marked `STALE`.
3. Confirm Code/Test has completed spec-code alignment or drift evidence.
4. Read every feature L2 AS-IS spec `§0 Baseline Delta` and validate each `change_type`:
   - `reuse`: references existing baseline facts; no baseline write.
   - `add`: adds a new spec, entrance, model, field, state, or error code.
   - `extend`: merges a compatible additive change while preserving old meaning.
   - `modify`: changes existing meaning, contract, constraint, or behavior and requires drift/test evidence.
   - `deprecate`: marks or removes obsolete facts and updates related indexes/tests.
   - Missing, invalid, or untraceable rows return `MANUAL_DECISION`.
5. Merge feature specs into matching baseline module paths according to Baseline Delta.
6. Copy entrance and flow overlays into baseline module directories as applicable.
7. Update baseline `index.md` references. Baseline indexes must not point at feature-only paths.

## Verification

1. Baseline files are updated.
2. Index paths are correct.
3. No required plan item is missing output evidence.
4. No stale item or unresolved spec/code/test drift remains.
5. Every merge action traces to `§0 Baseline Delta`.
