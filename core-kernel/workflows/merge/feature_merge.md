# Feature Merge

> Role: Reviewer. Merge accepted feature overlay specs into baseline after verification.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/code_contract.md`
- `shiki_context/modules/{module}/index.md`

## Steps

1. Confirm every required plan item has output_files.
2. Confirm Contract Version matches the plan metadata.
3. Copy accepted feature design artifacts into matching baseline module paths.
4. Copy entrance and flow overlays into baseline module directories.
5. Update baseline `index.md` references.

## Verification

1. Baseline files are updated.
2. Index paths are correct.
3. No required plan item is missing output evidence.
