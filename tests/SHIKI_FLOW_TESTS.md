# Shiki v4 Flow Regression Scenarios

These scenarios are the manual regression contract for workflow, Task Contract,
context-loading, and gate changes.

## Shared Kernel

### Scenario: Canonical and Alias Contracts remain distinct

Given every YAML file under `core-kernel/runtime/task_contracts/`
When the contract inventory is validated
Then every Canonical Contract has `kind`, `id`, `stage`, `goal`, `inputs`, and one `workflow_ref`
And every Alias Contract has only `kind`, `id`, and `canonical`
And Alias resolution terminates at one valid Canonical Contract.

### Scenario: one Plan row is one Task

Given a Plan with several ready rows
When `shiki task next` runs
Then exactly one row is selected
And dependencies are checked before selection
And the Context Envelope contains the resolved Canonical Contract and workflow
And duplicate documents with identical content are loaded only once.

### Scenario: completion is output-controlled

Given an active prepared Task
When `shiki task complete` receives every declared output and those files exist
Then `output_files` is updated and `active_task.md` advances
But when the Provider returns `BLOCKED`, `FAILED`, or `MANUAL_DECISION`
Then the completion tool is not called and the Plan ledger is unchanged.

### Scenario: deterministic Plan expansion

Given a Canonical Task that may discover child work
When it calls `shiki plan add-item` with a valid owned child
Then the child is inserted deterministically with validated dependencies
And a Provider cannot write arbitrary Plan rows directly.

## CLI automatic track

### Scenario: fresh Task sessions

Given `provider.name` selects Codex or Claude
When `shiki next` executes two ready Tasks
Then each Task starts a new Provider process
And no provider conversation state is reused between Tasks
And every process receives only its prepared Context Envelope.

### Scenario: Review is isolated

Given a Task completes successfully at the configured Review boundary
When the CLI triggers Review
Then Review starts in a separate fresh Provider process
And Codex uses a read-only sandbox or Claude uses `plan` permission mode
And its first line is one of `PASS`, `CHANGE_REQUEST`, `BLOCKED`, `FAILED`, or `MANUAL_DECISION`
And `CHANGE_REQUEST` stops orchestration without turning Review prose into edits.

### Scenario: Provider status is mandatory

Given a Provider process returns output
When the first non-empty line is not an allowed status
Then the CLI treats the result as failed
And no Task completion state is written.

## Prompt manual track

### Scenario: execute in the current Coding Agent session

Given a project-local adapter and an active developer session
When the developer invokes `/shiki-next`
Then the adapter calls `shiki task next`
And executes exactly one returned Context Envelope in that same session
And calls `shiki task complete` only on `PASS`
And stops after the Task.

### Scenario: Review timing belongs to the developer

Given a Prompt-track Task has completed
When the developer has not invoked `/shiki-review`
Then the adapter does not start Review
And it does not start a phase wave, batch, worker loop, or fresh session.

### Scenario: adapter manifests expose only Prompt semantics

Given adapters are installed for Codex, Claude Code, Gemini CLI, and OpenCode
When their manifests are inspected
Then `collaboration_track` is `prompt_manual`
And `execution_modes` is only `single_task_current_session`
And `session_owner` and `review_owner` are `developer`
And no Shiki-managed phase-wave agent remains.

## Init and Scan

### Scenario: scan seeds Kernel-routable Init work

Given initialized Shiki context and source configuration
When `scan.py` seeds an empty Init Plan
Then controller inspection rows use `init/inspect_controller.yaml`
And one `init/sync_plan.yaml` row depends on the inspections
And the Plan uses only `id`, `phase`, `target`, `module`, `depends_on`, `contract`, and `output_files`.

### Scenario: Flow is optional

Given an entrance is discovered
When no explicit Flow Task is added to the Plan
Then no Flow spec is created implicitly
But when a Flow Task is added through the Kernel
Then it routes through the Canonical `init/flow.yaml` Contract.

## Feature, Test, Sync, and Doctor

### Scenario: feature bootstrap routes through Design

Given a new feature workspace
When its bootstrap Plan is routed
Then the first Canonical Task is `design/design_init.yaml`
And expanded rows keep the six v4 columns
And Design reads baseline/source facts before adding new concepts.

### Scenario: Test reports a status-first result

Given a Test `run` Task
When the project verifier passes
Then the Provider returns `PASS: <summary>` and may complete with a permitted no-file reason
But when the verifier fails
Then it returns `BLOCKED: <reason>` with evidence and no ledger mutation.

### Scenario: Sync uses a bounded published-v4 Plan

Given Code-to-Spec drift may affect several leaf specs
When Sync planning runs
Then it writes bounded `sync_plan.md` items
And each apply Task updates at most one leaf through `sync/apply_leaf.yaml`
And every changed fact traces to source evidence.

### Scenario: Doctor separates diagnosis from repair

Given a consistency issue
When Doctor planning runs
Then diagnosis is read-only and produces explicit repair items
And each repair item applies only one confirmed correction
And unrelated files remain unchanged.

## Merge

### Scenario: Merge requires completed upstream outputs

Given a feature reaches Merge
When any required Design, Code, or Test Task lacks valid `output_files`
Then Merge is blocked
Otherwise feature overlay specs may be reconciled into the baseline and verified.
