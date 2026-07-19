# Init Sync Plan Workflow

Expand completed Init leaf outputs into bounded project-level synchronization tasks.

## Steps

1. Require all mandatory Init leaf items to be complete. Flow is optional.
2. Collect completed entrance and optional flow routes from the Plan and indexes without loading full flow bodies.
3. Add missing `init/sync_project_artifact.yaml` rows for architecture, integration, ubiquitous language, tech stack, tech debt, and project index.
4. Each row owns one target, depends on the current sync-plan item, and starts with empty `output_files`.
5. Deduplicate by Canonical Contract plus target and do not edit project spec bodies.

## Verification

- Each project target has one bounded row.
- New rows use the Canonical Contract.
- The current item records only `shiki_context/workspace/_plan.md`.
