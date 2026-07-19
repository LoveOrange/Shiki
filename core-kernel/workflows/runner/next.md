# Runner Next

Defines single-Task dispatch for both collaboration tracks. CLI automatic mode and Prompt manual mode call the same Kernel Task Tools.

## Inputs

- Optional item id such as `D2`.
- CLI automatic mode calls Kernel `next_task` directly.
- Prompt manual mode calls `shiki task next [item]` in the developer's current Coding Agent session.
- A Provider receives only the returned Context Envelope and must not route another item.

## Steps

1. `next_task` parses the active Plan once and validates scope, dependencies, target, and required inputs. A missing or empty Init Plan returns the synthetic `init-plan` Task; a missing Sync Plan returns `sync-plan`.
2. Select one Task by `active_task.next`, explicit item, then the first ready Plan row. Route a unique producer when required input is missing.
3. Resolve Canonical/Alias Contract deterministically and build a Context Envelope from the current Task, direct dependencies, Plan metadata, required content, optional paths, and Workflow.
4. Execute exactly that Workflow. The Provider or current interactive Agent must not select another Task.
5. After verification, call `complete_task`:
   - fixed output: `shiki task complete <task_id>`;
   - flexible code output: repeat `--output <path>` for major files;
   - no change: `--noop <reason>`;
   - narrow Plan expansion: `shiki plan add-item ...`.
6. Post-check the first Provider line and the Plan ledger. File outputs must exist, NOOP must include a reason, and failure statuses must not enter `output_files`.
7. Update `_plan.md.output_files`; for feature scope also update `active_task.next`.
8. Stop after one Task. Prompt mode returns control to the developer. CLI mode may start a fresh Provider session for the next Task or a separate Review session according to `orchestrate.granularity`.

## Forbidden

- Do not execute multiple Plan items in one Agent session.
- Do not duplicate Router or completion logic in Prompt/CLI adapters.
- Do not treat `active_task.md` or `last_run.md` as completion truth.
- Do not write `BLOCKED`, `FAILED`, `MANUAL_DECISION`, or `CHANGE_REQUEST` into `output_files`.
