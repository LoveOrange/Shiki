# Doctor Plan

> Role: Doctor Planner. Diagnose read-only and create a bounded repair Plan only after explicit developer confirmation.

## Steps

1. Classify workspace-ignore, recovery, legacy migration, adapter contract, context interface, Plan schema, spec health, or noop issues.
2. Report diagnosis, deterministic repairs, Manual Decision items, and backup advice without edits.
3. Stop unless repair/migration is explicitly confirmed.
4. After confirmation, create `workspace/doctor_plan.md` with columns:
   `id | phase | target | source_files | depends_on | contract | output_files`.
5. Add only deterministic, reversible rows using `doctor/apply_item.yaml`.
6. Put ambiguous ownership, business fact changes, destructive work, and Git index operations in Manual Decision.
7. Stop without executing a row.

## Verification

- Unconfirmed diagnosis changed no files.
- Confirmed planning changed only `workspace/doctor_plan.md`.
- Executable rows start with empty `output_files`.
