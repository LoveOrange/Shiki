# Tech Contract: shiki-core

Applies when maintaining Shiki's own Markdown protocols, workflows, templates,
and Python scripts.

## Rules

- Artifacts should express protocols, state machines, file contracts, and checks.
- Do not assume Java DDD layering inside core.
- Markdown files should keep executable, checkable, routable information only.
- Workflows should be small and single-purpose.
- Python scripts should use the standard library unless a dependency is justified.
- State comes from files, metadata, and tests, not conversation memory.
- Human approval, review, and verification gates cannot be replaced by the model.
