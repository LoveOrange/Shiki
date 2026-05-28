# Doctor Plan

> Role: Doctor Planner. Diagnose context-store maintenance issues read-only by default. Write a bounded repair plan only after explicit user confirmation.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- current scope `_plan.md` when present
- `shiki_context/project/index.md` when present
- necessary module or feature indexes

Check file existence as needed, but do not read whole business spec bodies for diagnosis.

## Steps

1. Identify the doctor mode:
   - `workspace_ignore`: `shiki_context/workspace/.gitignore` is missing or not using the current policy.
   - `recover`: a plan row lacks `output_files`, but the corresponding leaf spec already exists.
   - `migrate_v2`: old paths or old lifecycle files are present.
   - `noop`: structure is current and no repair is needed.
2. First output a read-only diagnosis: structure status, recommended mode, deterministic repair items, Manual Decision items, and backup advice.
3. If the user has not explicitly confirmed repair or migration, stop with no file changes.
4. After confirmation, create or update `shiki_context/workspace/doctor_plan.md`:

```markdown
# Doctor Plan

## Meta

- **Mode**: [workspace_ignore / recover / migrate_v2]
- **Confirmation**: [repair confirmed / migration confirmed]
- **Backup**: [required / not required + path suggestion]

## Target Outputs

| id | phase | target | source_files | depends_on | contract | output_files |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DR1 | Init | `shiki_context/workspace/.gitignore` | - | - | `core-kernel/runtime/task_contracts/doctor/apply_item.yaml` | |

## Manual Decision

| source | candidates | reason |
| :--- | :--- | :--- |
```

5. Only deterministic, reversible, bounded work may become executable rows.
6. Ambiguous ownership, business fact changes, destructive operations, or Git index work must go to Manual Decision.
7. Stop without executing repair rows.

## Verification

1. Unconfirmed runs do not change files.
2. Confirmed planning changes only `workspace/doctor_plan.md`.
3. Every executable row has target, contract, and empty output_files.
4. Business spec bodies are not modified during planning.
