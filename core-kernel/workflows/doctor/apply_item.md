# Doctor Apply Item

> Role: Doctor Executor. Execute exactly one confirmed deterministic item from `doctor_plan.md`, then stop.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/doctor_plan.md`
- first row whose `output_files` is empty and whose contract points to `doctor/apply_item.yaml`
- files named by that row target and source_files

Do not load a whole business spec directory to infer migration ownership.

## Steps

1. Confirm `doctor_plan.md` metadata records explicit repair or migration confirmation; otherwise return `BLOCKED: confirmation required`.
2. Select the first ready doctor item; if none exists, return `NOOP`.
3. Execute exactly one deterministic repair:
   - `workspace_ignore`: create or update only `shiki_context/workspace/.gitignore`.
   - `recover`: fill `_plan.md` `output_files` only with existing valid file paths.
   - `migrate_v2`: execute only file moves, renames, or index path replacements listed in `doctor_plan.md`.
4. Stop and mark `MANUAL_DECISION` or `BLOCKED` if target/source is missing without explanation, ownership is ambiguous, business spec body rewrite is required, or the operation requires deletion, Git index cleanup, global config changes, or sensitive paths.
5. On success, write changed file paths to the current row `output_files`.
6. Stop without executing the next row.

## Verification

1. Only one doctor item was processed.
2. Changed files match the current row target/source.
3. Business spec bodies were not modified unless the confirmed row explicitly performs index path replacement.
4. No `git rm`, `git reset`, checkout, global config edit, or deletion operation was executed.
