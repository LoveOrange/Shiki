# Workflows

Workflows are concise human-readable procedures referenced by task contracts.
They do not replace task contracts. A runner selects one plan item, or an
explicit safe batch of plan items, loads each YAML contract, then loads the
workflow named by each `workflow_ref`.

Routing overview:

```text
core-kernel/runtime/context_loading.md       context loading budget and layering protocol
core-kernel/runtime/task_contracts/**/*.yaml machine-readable task contracts
core-kernel/workflows/**/*.md                self-contained human-readable workflows
core-kernel/workflows/runner/*.md            select and route one plan item, or a safe explicit batch
core-kernel/workflows/sync/*.md              plan Code -> Spec sync, then apply one leaf at a time
core-kernel/workflows/doctor/*.md            diagnose read-only, then repair one confirmed item at a time
shiki_context/constitution/tech_contracts/   project-owned tech contract slices
L2 AS-IS leaf specs                          default Code/Test fact source
code_contract.md                             optional implementation slice, not a replacement for L2 specs
```

Every workflow should include:

- `## Load`
- `## Steps`
- `## Output` when it writes files
- `## Verification`

Do not load legacy docs, the full cheatsheet, or a whole module file tree by
default. `sync` and `doctor` follow the one-item rule even when feature work uses
the optional batch runner.
