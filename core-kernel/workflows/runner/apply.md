# Runner Apply

> Role: Compatibility entry. Current semantics are the same adaptive execution
> session used by `next`.

## Load

- `core-kernel/runtime/context_loading.md`
- `core-kernel/runtime/execution_session.md`
- `core-kernel/workflows/runner/next.md`
- `shiki_context/workspace/active_task.md`
- current scope plan:
  - Init stage: `shiki_context/workspace/_plan.md`
  - Feature stage: `shiki_context/features/{feature}/_plan.md`
  - temporary maintenance plan: `shiki_context/workspace/*_plan.md`

## Steps

1. Run the same coordinator preflight as `next`.
2. Select an adaptive execution window and topology from adapter metadata, plan
   state, context budget, and stop conditions.
3. Execute items through task contracts and workflow refs.
4. Run review and verification gates before marking any item done.
5. Stop at the same stop boundaries as `next`.
6. State that this run used the apply compatibility entry.

## Forbidden

- Do not preserve old one-item semantics when the adaptive session policy safely
  allows more progress.
- Do not skip review gates, task contracts, L2 specs, alignment checks, or
  drift/test gates.
- Do not load the full prompt docs, full module tree, or full source tree by
  default.
