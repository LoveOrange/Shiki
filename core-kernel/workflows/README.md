# Workflows

Workflows are concise procedures referenced by Canonical Task Contracts. They
do not own input manifests and never replace the Contract or Context Envelope.

```text
core-kernel/runtime/task_contracts/**/*.yaml  Canonical and Alias Contracts
core-kernel/workflows/**/*.md                 execution and verification steps
core-kernel/workflows/runner/next.md          shared single-Task protocol
shiki_context/constitution/tech_contracts/    project-owned stack rules
```

Every executable workflow should include `## Steps` and `## Verification`, plus
`## Output` when it writes files. Inputs and references are loaded exclusively
from the resolved Canonical Contract and the Kernel-built Context Envelope.

Do not load legacy docs, the full cheatsheet, or a whole module tree by default.
Init, feature, Sync, Doctor, Test, and Merge all follow the same one-Task Kernel
boundary.
