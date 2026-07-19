# Task Contracts

Task Contracts are machine-readable atomic task signatures stored as YAML.

A Canonical Contract contains only:

- `kind`, `id`, `stage`, and `goal`;
- `inputs[]`, where every entry has exactly `path` and `required`;
- optional fixed `output.path`;
- `workflow_ref`.

Contracts do not contain references, checks, done conditions, tech-stack rules, file modes, Review state, or retry policy. Workflow owns execution, self-checks, and project validation. Orchestrator owns dispatch boundaries and Review.

Alias Contracts contain only `kind: alias`, `id`, `canonical`, and optional static `bindings`. Aliases must resolve directly to one Canonical Contract; chains are rejected. New Plans write Canonical relative refs. Aliases exist only for compatibility.

Required-input routing uses Canonical `output.path` ownership. A unique ready producer can be routed automatically; ambiguous ownership returns MANUAL_DECISION; no owner returns BLOCKED.

Atomic maintenance contracts:

- `init/plan.yaml` creates the initial Init Plan.
- `init/inspect_controller.yaml` expands one Controller/API group.
- `init/entrance_spec.yaml` writes one entrance aggregate.
- `init/sync_plan.yaml` adds bounded project sync rows.
- `init/sync_project_artifact.yaml` writes one project artifact.
- `sync/plan.yaml` creates a bounded Code-to-Spec Plan.
- `sync/apply_leaf.yaml` updates one leaf spec.
- `doctor/plan.yaml` creates an authorized repair Plan.
- `doctor/apply_item.yaml` performs one deterministic repair.
- `test/run.yaml` runs verification and reports; the Orchestrator chooses the next Task.
