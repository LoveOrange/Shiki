# Shiki Command Cheatsheet

Install a project-local adapter first when your coding tool supports it. The
preferred Code Agent path is to ask the tool you are already using:

```text
Install github.com/LoveOrange/Shiki in this project as shiki/, initialize Shiki,
and install the Shiki adapter for the coding tool I am using now. Preserve any
existing project changes, and tell me which files were created or updated.
```

If `shiki/` already exists, ask for the adapter repair path:

```text
Install or repair the Shiki adapter for my current coding tool from the existing
shiki/ directory. Reload the tool command surface if needed.
```

To update an existing install, ask the same tool:

```text
Update the Shiki install in this project to the latest github.com/LoveOrange/Shiki
version. First identify whether shiki/ is a submodule, subtree, or plain checkout.
Record the current Shiki commit, update it using the project's existing install
style, then rerun Shiki init and repair the adapter for my current coding tool.
Preserve unrelated project changes. When finished, report the old commit, new
commit, upstream Shiki commits included in the update, and any project-local
Shiki files or adapter files that were created or updated.
```

Manual commands below assume Shiki is mounted as `shiki/` in the consumer
project.

```bash
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool all
```

Use a single target to install one adapter:

```bash
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool claude
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool gemini
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool opencode
```

Primary tool-native commands:

```text
/shiki-init
/shiki-status
/shiki-next
/shiki-modify <target>
/shiki-review
/shiki-sync
/shiki-doctor
```

Generated project-local files:

| tool | command files | extra files |
| :--- | :--- | :--- |
| Codex | `.codex/prompts/shiki-*.md` | `.codex/skills/shiki/SKILL.md` |
| Claude Code | `.claude/commands/shiki-*.md` | `.claude/agents/shiki-phase-wave.md` |
| Gemini CLI | `.gemini/commands/shiki-*.toml` | - |
| OpenCode | `.opencode/commands/shiki-*.md` | `.opencode/agents/shiki-*.md` |

Command invocation after install:

| tool | invoke | active-session note |
| :--- | :--- | :--- |
| Codex | `/shiki-status`, `/shiki-next`, `/shiki-modify <target>` | restart or reload the project session if prompts/skills were loaded before install |
| Claude Code | `/shiki-status`, `/shiki-next`, `/shiki-modify <target>` | restart or reload commands after `.claude/commands/` changes |
| Gemini CLI | `/shiki-status`, `/shiki-next`, `/shiki-modify <target>` | run `/commands reload` after `.gemini/commands/` changes |
| OpenCode | `/shiki-status`, `/shiki-next`, `/shiki-modify <target>` | restart or reload the project session after `.opencode/commands/` changes |

`/shiki-next` is the user-facing runner. It advances conservatively by one ready
item by default. Strong adapters may use bounded batch, phase-wave, or subagent
execution internally only when Core Kernel stop rules allow it; each selected
item still loads its own task contract and updates its own `output_files` only
after verification passes. Merge remains root-controlled by default.

The prompt blocks below are fallback entries for agents without an installed
adapter or for manually inspecting adapter behavior.

## 1. scan

Run repository discovery and build the initial Shiki baseline.

```text
Use Shiki scan.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/next.md
#/shiki_context/workspace/active_task.md
#/shiki_context/workspace/_plan.md

Steps:
1. Read shiki.config.yaml for src_root, base_package, and tech_stacks.
2. Discover controller, listener, job, scheduler, and message entry points.
3. Write shiki_context/workspace/_plan.md with init.entrance tasks and one init.sync task.
4. For each ready init.entrance task, trace the call chain and write module entrances and flows.
5. Run init.sync to aggregate dependencies, integration, and tech debt.
6. Stop after the plan output_files are updated.
```

## 2. new feature

Create a feature workspace.

```bash
python shiki/tools-skills/scripts/new_feature.py --taskid <TASKID>
```

Then fill in `shiki_context/features/<TASKID>/design_brief.md`.

## 3. status

Inspect current progress and identify the next runnable item.

```text
Use Shiki status.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki_context/workspace/active_task.md

Steps:
1. Read active_task.md.
2. Read the current scope _plan.md.
3. Check depends_on and output_files.
4. Report the next runnable item, gate status, blockers, and missing files.
5. Do not execute the item.
```

## 4. next

Execute exactly one ready plan item.

```text
Use Shiki next.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/next.md
#/shiki_context/workspace/active_task.md

Steps:
1. Read active_task.md and the current _plan.md.
2. Select the first item whose dependencies are satisfied and output_files are empty or marked STALE.
3. Load its task contract from core-kernel/runtime/task_contracts/.
4. Load the workflow_ref, required template, and selected tech contract slices.
5. Execute only that workflow.
6. Update output_files for the completed item.
7. Stop.
```

## 4a. apply

Compatibility entry. Current semantics are the same as `next`.

```text
Use Shiki apply.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/apply.md
#/shiki_context/workspace/active_task.md

Steps:
1. Execute one ready item exactly as `next` would.
2. State that this run used the apply compatibility entry.
3. Stop after one item.
```

## 4b. batch

Fallback/internal entry for a bounded sequence of safe ready plan items. With
tool-native adapters, batch execution is an internal strategy behind
`/shiki-next`, not a primary user-facing command.

```text
Use Shiki batch.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/batch.md
#/shiki_context/workspace/active_task.md

Steps:
1. Read active_task.md and the current _plan.md.
2. Select a bounded batch using runner/batch.md Selection Policy.
3. State the claimed item ids, why they are safe to batch, and the verification that will close the batch.
4. For each item, load its task contract from core-kernel/runtime/task_contracts/ and execute its workflow_ref sequentially.
5. Update output_files after each completed item.
6. Stop at any batch stop condition, failed check, or required user decision.
7. Report completed item ids, blocked item id if any, modified files, and verification.
```

`Use Shiki auto` is an alias for this prompt. The model may choose a smaller
batch than requested, but it must not cross batch stop conditions.

## 5. review

Review produced files and implementation alignment.

```text
Use Shiki review.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki_context/workspace/active_task.md

Check:
1. The active _plan.md item and its output_files.
2. The relevant L2 AS-IS leaf specs, design_brief.md, optional implementation slice, and changed code.
3. Whether code follows the current specs and selected tech contracts.
4. Whether tests cover happy path, boundaries, errors, permissions, idempotency, concurrency, and integration.

Output findings first, ordered by severity. Do not change files unless asked.
```

## 6. modify

Make a bounded change to existing code or specs.

```text
Use Shiki modify.

Input:
- Target file(s): <paths>
- Requested change: <change>

Steps:
1. Load active_task.md and direct specs related to the target.
2. Determine whether the change is code-only, spec-only, or affects downstream items.
3. Edit only the required files.
4. Mark downstream completed items `STALE` when the change affects them.
5. Run the smallest meaningful verification.
```

## 7. doctor

Repair local Shiki context structure without changing business facts.

```text
Use Shiki doctor.

Check:
1. shiki_context/workspace/
2. shiki_context/project/
3. shiki_context/modules/
4. shiki_context/features/
5. shiki_context/constitution/tech_contracts/

Default to read-only diagnosis. After explicit confirmation, create
shiki_context/workspace/doctor_plan.md and execute one deterministic item at a time.
Do not move, delete, rewrite, or untrack existing user files without approval.
```

## 8. sync

Plan and apply bounded Code -> Spec synchronization.

```text
Use Shiki sync.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/runtime/task_contracts/sync/plan.yaml
#/shiki/core-kernel/runtime/task_contracts/sync/apply_leaf.yaml
#/shiki_context/workspace/active_task.md

Steps:
1. Use only the user-specified changed source files, module, feature, or git diff scope.
2. First create or update shiki_context/workspace/sync_plan.md.
3. Do not edit specs during planning.
4. Then execute only the first ready sync_plan item.
5. Update exactly one target leaf spec from direct source evidence.
6. Mark ambiguous mappings MANUAL_DECISION instead of inventing facts.
```

## 9. fix

Analyze an exception stack and route the repair.

```text
Use Shiki fix.

Input:
- Exception stack: <paste stack>

Steps:
1. Read the stack and infer the failing source location.
2. Load the related source and current specs only as needed.
3. Identify whether the issue is code -> code, code -> spec, or feature -> spec.
4. Recommend the next write path: modify, sync, or explicit feature plan.
5. Do not create or modify plans unless explicitly asked.
```

## 10. publish docs

Publish Markdown specs as an offline HTML site.

```bash
python shiki/tools-skills/skills/spec-to-html/scripts/publish_docs.py <input-path> --title "Shiki Spec" --fail-on-broken-links
```

## 11. publish pretty Shiki spec

Generate an L0 human-friendly spec site from Shiki L1 consensus specs.

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --title "Shiki Spec" --fail-on-broken-links
```

For one feature:

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --feature <TASKID> --title "<TASKID> Spec" --fail-on-broken-links
```
