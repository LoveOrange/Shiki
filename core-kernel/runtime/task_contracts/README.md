# Task Contracts

`core-kernel/runtime/task_contracts/` stores machine-readable atomic task contracts in YAML.

They are the routing truth and describe:

- task goal
- inputs and references
- target output
- checks
- test specs and check rules
- retry policy
- done condition
- review and evidence expectations through the execution session

`core-kernel/workflows/*.md` remain human-readable prompt views; YAML task contracts carry the executable routing truth.

## Contract Routing

The model does not need a separate task-kind registry. Runtime reads the current plan item `contract` column and loads that YAML.

Maintenance rules:

- User-facing commands should not expose a private task-kind list.
- YAML contracts no longer declare a separate task-kind field; the contract path and `id` are the route.
- Plan rows for multi-step commands use only `contract` to distinguish sync, doctor, and similar actions.

These contracts must also stay atomic:

- `sync/plan.yaml` creates only a bounded Code -> Spec sync plan and does not edit specs.
- `sync/apply_leaf.yaml` syncs exactly one leaf spec.
- `doctor/plan.yaml` diagnoses read-only by default and creates a repair plan only after confirmation.
- `doctor/apply_item.yaml` executes exactly one deterministic repair item.

`/shiki-next` may advance several ready contract-backed items inside one
adaptive execution session, but the session must still load each task contract
separately and record each item's status, output_files, evidence, and
review_result independently when those plan columns exist.
