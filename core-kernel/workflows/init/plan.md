# Init Plan Workflow

Create the initial `workspace/_plan.md` for brownfield baseline discovery.

## Steps

1. Require `active_task.stage = Init`; otherwise return `BLOCKED: scan requires Init stage`.
2. Read configured source roots and tech stacks. Return BLOCKED when the source root does not exist.
3. Perform lightweight entrance discovery only: Controller/API groups, stable module candidates, and source references.
4. Create or update `workspace/_plan.md` with columns `id | phase | target | module | depends_on | contract | output_files`.
5. Add one `init/inspect_controller.yaml` row per Controller/API group, sorted by relative source path, then add `sync-plan` with `init/sync_plan.yaml` depending on all inspect rows.
6. New rows use Canonical relative Contract refs and empty `output_files`.
7. Do not create entrance or flow leaf specs.

## Output

- `shiki_context/workspace/_plan.md`

## Verification

- Every row has the same number of cells as the header.
- Initial `output_files` cells are empty.
- New rows use Canonical relative refs.
- No leaf spec was created or changed.
