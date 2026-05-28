# Sync Plan

> Role: Sync Planner. Identify a bounded Code -> Spec sync scope and create a workspace temporary plan. This workflow does not edit spec bodies.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- user-supplied changed files, module, feature, or git diff scope
- `shiki_context/project/index.md`
- `shiki_context/modules/{module}/index.md` when module scope is known
- `shiki_context/features/{feature}/index.md` and `_plan.md` when feature scope is active

Do not load a whole module directory, whole source tree, every flow file, or the
full prompt docs by default.

## Steps

1. Normalize the sync input:
   - If the user names source files, those files are the upper bound.
   - If the user names only a module, use `git diff --name-only`, module index, and source path rules to produce candidate files.
   - If the candidate set is still broad, return `BLOCKED: sync scope too broad` and ask for a narrower entry, scenario, or file set.
2. Collect lightweight evidence for each candidate source file: path, class, method, public signature, DTO/Entity fields, states, and error codes.
3. Use indexes and deterministic symbol/path searches to map candidates to leaf specs:
   - `entrances/{entrance}.md` for public API, request/response, and error semantics.
   - `flows/{scenario}.md` for transitions, branches, transactions, and exception paths.
   - `designs/model.md` for entities, value objects, fields, and states.
   - `designs/component.md` for responsibilities, interface signatures, and dependency direction.
4. Write uncertain mappings to `Manual Decision`; do not create executable rows for them.
5. Create or update `shiki_context/workspace/sync_plan.md`:

```markdown
# Sync Plan

## Meta

- **Scope**: [source files / module / feature]
- **Created From**: [user input or git diff range]

## Target Outputs

| id | phase | target | source_files | depends_on | contract | output_files |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| S1 | Code | `modules/{module}/entrances/{entrance}.md` | `src/.../X.java` | - | `core-kernel/runtime/task_contracts/sync/apply_leaf.yaml` | |

## Manual Decision

| source | candidates | reason |
| :--- | :--- | :--- |
```

6. Stop without executing any `sync/apply_leaf.yaml` row.

## Verification

1. Every executable row has target, source_files, contract, and empty output_files.
2. Every target is a single leaf spec, not a module directory.
3. Uncertain mappings are recorded as Manual Decision, not current valid fact.
4. This workflow does not modify `shiki_context/modules/**`, `shiki_context/features/**`, or source files.
