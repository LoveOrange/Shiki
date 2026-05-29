# Shiki Tool Adapter Contract v1

## Status

- Contract Version: v1
- Owner: User Interface
- Applies To: Codex, Claude Code, Gemini CLI, OpenCode

This contract defines the shared command surface for tool-native Shiki adapters.
Adapters translate native tool commands, skills, agents, or project-local files
into Shiki Core Kernel execution. Shiki Core remains the source of truth for plan
routing, task contracts, workflow binding, context loading, evidence, and gate
state.

Adapters must not duplicate phase rules, task contract semantics, batch rules,
merge rules, or context loading policy. They load and call the Core Kernel
documents and scripts listed below.

## Adapter Manifest

Each installed adapter must declare these capability flags in its project-local
adapter metadata:

| flag | meaning |
| :--- | :--- |
| `supports_slash_commands` | The tool can expose user-facing `/shiki-*` commands directly. |
| `supports_skills` | The tool can install reusable command bodies, skills, rules, or prompt files. |
| `supports_subagents` | The tool can delegate work to child agents while a root agent retains state control. |
| `supports_project_local_install` | The tool can be configured from files inside the consumer project. |

The manifest also records:

| field | meaning |
| :--- | :--- |
| `adapter_contract_version` | Must be `v1` for this contract. |
| `tool` | One of `codex`, `claude-code`, `gemini-cli`, or `opencode`. |
| `installed_commands` | Native command names mapped to the canonical commands below. |
| `execution_modes` | Supported internal modes from this contract. |
| `source_root` | Path to the mounted Shiki framework, normally `shiki/`. |
| `context_root` | Path to the consumer context store, normally `shiki_context/`. |

## Tool Capability Matrix

Adapters must encode the target tool capability row in their generated
project-local manifest. The matrix is descriptive; Core Kernel task contracts
remain authoritative for actual execution and stop decisions.

| tool | manifest `tool` | slash commands | skills or prompt files | subagents | project-local install | allowed execution modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Codex | `codex` | yes | yes | no | yes | `single_item`, `bounded_batch` |
| Claude Code | `claude-code` | yes | no | yes | yes | `single_item`, `bounded_batch`, `phase_wave`, `subagent_delegation` |
| Gemini CLI | `gemini-cli` | yes | no | no | yes | `single_item`, `bounded_batch` |
| OpenCode | `opencode` | yes | yes | yes | yes | `single_item`, `bounded_batch`, `phase_wave`, `subagent_delegation` |

## Canonical Commands

Adapters expose exactly these user-facing command names unless a host tool
requires a documented alias:

| command | purpose |
| :--- | :--- |
| `/shiki-init` | Initialize or repair the project-local Shiki context scaffold. |
| `/shiki-status` | Report current scope, next runnable item, gates, and blockers without changing files. |
| `/shiki-next` | Execute the next allowed Shiki plan work through Core Kernel contracts. |
| `/shiki-modify <target>` | Make a bounded user-requested change to existing code or specs. |
| `/shiki-review` | Review produced files and implementation alignment without changing files. |
| `/shiki-sync` | Plan and apply bounded Code -> Spec synchronization. |
| `/shiki-doctor` | Diagnose or repair Shiki context structure. |

Adapters may expose host-tool aliases, but help text must point back to these
canonical command names.

## Command To Core Mapping

Every adapter command must load this contract first, then the listed Core Kernel
entry points. Command prompts may summarize the user intent, but they must not
replace the referenced workflow or task contract logic.

| command | Core Kernel entry points | default write behavior |
| :--- | :--- | :--- |
| `/shiki-init` | `tools-skills/scripts/init.py`; `core-kernel/templates/workspace/.gitignore`; selected `tech-stacks/tech-contracts/<stack>/` | Creates or repairs deterministic Shiki context scaffolding. |
| `/shiki-status` | `core-kernel/runtime/context_loading.md`; `shiki_context/workspace/active_task.md`; current scope `_plan.md` | Read-only. |
| `/shiki-next` | `core-kernel/workflows/runner/next.md`; selected `core-kernel/runtime/task_contracts/**/*.yaml`; selected contract `workflow_ref`; `core-kernel/workflows/runner/batch.md` only for non-`single_item` modes | Writes only outputs owned by selected ready item or allowed internal batch/wave items. |
| `/shiki-modify <target>` | `core-kernel/runtime/context_loading.md`; direct specs and source files for the target; related task contracts when planned work is affected | Bounded edits to requested targets and stale-state updates only when required. |
| `/shiki-review` | `core-kernel/runtime/context_loading.md`; relevant L2 AS-IS leaf specs; relevant changed source or spec files | Read-only unless the user explicitly changes the task. |
| `/shiki-sync` | `core-kernel/runtime/task_contracts/sync/plan.yaml`; `core-kernel/runtime/task_contracts/sync/apply_leaf.yaml` | Creates or updates sync plan first, then at most one target leaf spec per apply step. |
| `/shiki-doctor` | `core-kernel/runtime/task_contracts/doctor/plan.yaml`; `core-kernel/runtime/task_contracts/doctor/apply_item.yaml` | Read-only by default; repairs at most one deterministic item after confirmation. |

## Execution Modes

The user-facing command stays stable while the adapter chooses one internal
execution mode:

| mode | allowed use |
| :--- | :--- |
| `single_item` | Default mode. Select and execute exactly one ready plan item. |
| `bounded_batch` | Execute several safe ready items only under `core-kernel/workflows/runner/batch.md` stop rules. |
| `phase_wave` | Claim a phase-bounded wave of items only when every item is independently routable by task contract and the same batch stop rules hold. |
| `subagent_delegation` | Delegate item execution to child agents only when the root agent owns plan state, dependency order, verification, and final ledger updates. |

`/shiki-next` defaults to `single_item`. Strong tools may use `bounded_batch`,
`phase_wave`, or `subagent_delegation` behind `/shiki-next`, but they must report
the selected mode before edits, update each item output separately, and stop at
the first Core Kernel stop condition. Merge remains root-controlled and must not
be delegated to autonomous subagents by default.

## Command Contract

### `/shiki-init`

Inputs:
- Optional target directory.
- Optional `shiki.config.yaml` values when the project has not been initialized.

Required loaded files:
- `shiki.config.yaml`
- `tools-skills/scripts/init.py`
- `core-kernel/templates/workspace/.gitignore`
- Selected `tech-stacks/tech-contracts/<stack>/` files.

Core mapping:
- Run or mirror `tools-skills/scripts/init.py`.
- Copy default tech contracts into `shiki_context/constitution/tech_contracts/`.

Outputs:
- `shiki_context/workspace/`
- `shiki_context/project/`
- `shiki_context/modules/`
- `shiki_context/features/`
- `shiki_context/constitution/tech_contracts/`

Stop conditions:
- Missing or ambiguous project root.
- Unsafe overwrite of existing user files.
- Missing selected tech stack.

Verification expectations:
- Confirm expected context directories and required seed files exist.
- Report no business facts were invented during initialization.

### `/shiki-status`

Inputs:
- Optional scope override.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- Current scope `_plan.md`.

Core mapping:
- Use the `status` plan strategy in `core-kernel/runtime/context_loading.md`.

Outputs:
- Current scope and stage.
- Next runnable item, if any.
- Gate state, blockers, missing files, and stale outputs.

Stop conditions:
- Missing `active_task.md`.
- Missing current plan.
- Ambiguous active scope.

Verification expectations:
- Read-only command. Report files inspected and confirm no edits were made.

### `/shiki-next`

Inputs:
- Optional execution-mode hint accepted by the host adapter.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `core-kernel/workflows/runner/next.md`
- `core-kernel/workflows/runner/batch.md` when using batch, phase wave, or subagent delegation.
- `shiki_context/workspace/active_task.md`
- Current scope `_plan.md`.
- Selected item `core-kernel/runtime/task_contracts/**/*.yaml`.
- Selected contract `workflow_ref`.

Core mapping:
- Select the first ready plan item from the current plan.
- Load the selected task contract before workflow text.
- Execute the workflow through the selected execution mode.

Outputs:
- Modified source, spec, or context files required by the selected item.
- Updated `output_files` for each completed item.
- Verification result for each completed item.

Stop conditions:
- No ready item.
- `BLOCKED` or `MANUAL_DECISION` item state.
- Missing required input, target, contract, workflow, or tech contract.
- Ambiguous ownership.
- Merge gate reached without explicit root-controlled merge execution.
- Failed verification.

Verification expectations:
- Run the task contract checks or the smallest meaningful project verification.
- Do not mark an item complete until verification passes.

### `/shiki-modify <target>`

Inputs:
- Required target path, plan item, module, feature, or source symbol.
- Required requested change from the user.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- Current scope `_plan.md`.
- Direct specs and source files related to the target.
- Related task contracts only when the change affects planned work.

Core mapping:
- Use the `modify` plan strategy in `core-kernel/runtime/context_loading.md`.
- Mark downstream completed items `STALE` when the requested change affects them.

Outputs:
- Bounded edits to requested targets.
- Updated plan state only when downstream work becomes stale.

Stop conditions:
- Missing target.
- Ambiguous target ownership.
- Request crosses unrelated scopes.
- Required design or product decision is missing.
- Verification fails.

Verification expectations:
- Run the smallest meaningful check covering the changed target.
- Report stale downstream items, if any.

### `/shiki-review`

Inputs:
- Optional target path, item id, feature, module, or diff scope.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- Current scope `_plan.md`.
- Relevant L2 AS-IS leaf specs.
- Relevant changed source or spec files.

Core mapping:
- Use the `review` plan strategy in `core-kernel/runtime/context_loading.md`.

Outputs:
- Findings first, ordered by severity.
- Missing test coverage and residual risk.

Stop conditions:
- Missing review target.
- Missing source/spec evidence needed for a finding.

Verification expectations:
- Read-only command. Do not edit files unless the user explicitly changes the task.

### `/shiki-sync`

Inputs:
- Required changed source files, module, feature, or bounded git diff scope.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `core-kernel/runtime/task_contracts/sync/plan.yaml`
- `core-kernel/runtime/task_contracts/sync/apply_leaf.yaml`
- `shiki_context/workspace/active_task.md`
- Source evidence named by the user scope.

Core mapping:
- First create or update `shiki_context/workspace/sync_plan.md`.
- Then apply exactly one ready sync leaf item through `sync/apply_leaf.yaml`.

Outputs:
- `shiki_context/workspace/sync_plan.md`
- At most one updated target leaf spec per apply step.

Stop conditions:
- Unbounded source scope.
- Ambiguous source-to-spec mapping.
- Missing direct source evidence.
- `MANUAL_DECISION` required.
- Verification fails.

Verification expectations:
- Confirm each synced fact traces to direct source evidence.
- Do not edit specs during sync planning.

### `/shiki-doctor`

Inputs:
- Optional context path or reported structural problem.
- Explicit user confirmation when a repair would modify files.

Required loaded files:
- `core-kernel/runtime/context_loading.md`
- `core-kernel/runtime/task_contracts/doctor/plan.yaml`
- `core-kernel/runtime/task_contracts/doctor/apply_item.yaml`
- `shiki_context/workspace/active_task.md`
- Context files needed to diagnose the reported structure.

Core mapping:
- Diagnose read-only by default.
- After confirmation, create `shiki_context/workspace/doctor_plan.md`.
- Apply at most one deterministic repair item through `doctor/apply_item.yaml`.

Outputs:
- Diagnosis.
- Optional `shiki_context/workspace/doctor_plan.md`.
- Optional bounded structural repair.

Stop conditions:
- Repair would delete, move, rewrite, or untrack user files without confirmation.
- Ambiguous ownership.
- Missing context root.
- Verification fails.

Verification expectations:
- Confirm repaired paths exist and remain routable.
- Report any unresolved `BLOCKED` or `MANUAL_DECISION` state.

## Status And Failure Reporting

Adapters must report Core Kernel stop states in a stable shape. Host tools may
format the report differently, but the content must be present.

### `BLOCKED`

Required fields:
- `state`: `BLOCKED`
- `command`
- `scope`
- `item_id`, when an item was selected
- `blocked_on`
- `missing_or_invalid_input`
- `files_inspected`
- `files_changed`
- `next_user_action`

Rules:
- Do not load unrelated context speculatively after a block is known.
- Do not mark the selected item complete.

### `MANUAL_DECISION`

Required fields:
- `state`: `MANUAL_DECISION`
- `command`
- `scope`
- `item_id`, when an item was selected
- `decision_needed`
- `options`
- `recommended_option`, when the evidence supports one
- `affected_items`
- `files_changed`

Rules:
- Ask for a focused decision.
- Do not invent missing business facts.
- Mark or report the plan item as `MANUAL_DECISION` when the active plan owns the decision.

### `VERIFICATION_FAILED`

Required fields:
- `state`: `VERIFICATION_FAILED`
- `command`
- `scope`
- `item_id`, when an item was selected
- `verification_command`
- `failure_summary`
- `files_changed`
- `retry_or_revert_guidance`

Rules:
- Keep the item incomplete.
- Report the failing check and the smallest useful next repair.
- Do not continue to later batch, wave, or delegated items.

## Installed Adapter File Expectations

A project-local installer must write only host-tool adapter files and metadata
needed to expose the canonical commands. Installed files must:

- Reference this contract version.
- Reference `core-kernel/runtime/context_loading.md`.
- Reference Core Kernel task contracts instead of embedding their business logic.
- Include command help for `/shiki-status`, `/shiki-next`, and `/shiki-modify <target>`.
- Keep generated adapter metadata separate from `shiki_context/` business facts.
- Be safe to regenerate without overwriting user-authored source files.

Regression checks must verify installed adapter files mention the canonical
commands, the adapter contract version, and Core Kernel command references.
