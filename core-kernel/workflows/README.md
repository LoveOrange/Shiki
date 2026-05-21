# Workflows

Workflows are concise human-readable procedures referenced by task contracts.
They do not replace task contracts. A runner selects a plan item, loads its YAML
contract, then loads the workflow named by `workflow_ref`.

Every workflow should include:

- `## Load`
- `## Steps`
- `## Output` when it writes artifacts
- `## Verification`
