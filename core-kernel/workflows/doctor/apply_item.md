# Doctor Apply Item

> Role: Doctor Executor. Execute exactly one confirmed deterministic repair row.

## Steps

1. Require explicit confirmation in `doctor_plan.md`.
2. Select one ready row or return NOOP.
3. Perform only the row's deterministic repair: workspace ignore, recovery from existing outputs, listed legacy move, Shiki-managed adapter regeneration, context routing repair, or deterministic index/metadata correction.
4. Return MANUAL_DECISION or BLOCKED for ambiguity, business-spec rewrites, deletion, Git index work, global configuration, or sensitive paths.
5. Record changed paths in the row's `output_files`.
6. Stop before another row.

## Verification

- One doctor row was processed.
- Changed files match the selected target/source.
- No destructive Git or global configuration operation ran.
