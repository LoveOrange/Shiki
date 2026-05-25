# Shiki Prompt Cheatsheet

Copy the relevant prompt into your AI coding agent. Paths assume Shiki is mounted
as `shiki/` in the consumer project.

## 1. scan

Run repository discovery and build the initial Shiki baseline.

```text
Use Shiki scan.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/apply.md
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
4. Report the next runnable item, blockers, and missing artifacts.
5. Do not execute the item.
```

## 4. apply

Execute exactly one ready plan item.

```text
Use Shiki apply.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki/core-kernel/workflows/runner/apply.md
#/shiki_context/workspace/active_task.md

Steps:
1. Read active_task.md and the current _plan.md.
2. Select the first item whose dependencies are satisfied and output_files are empty.
3. Load its task contract from core-kernel/runtime/task_contracts/.
4. Load the workflow_ref, required template, and selected tech contract slices.
5. Execute only that workflow.
6. Update output_files for the completed item.
7. Stop.
```

## 5. review

Review produced artifacts and implementation alignment.

```text
Use Shiki review.

Load:
#/shiki/core-kernel/runtime/context_loading.md
#/shiki_context/workspace/active_task.md

Check:
1. The active _plan.md item and its output_files.
2. The relevant code_contract.md, design_brief.md, leaf specs, and changed code.
3. Whether code follows the declared contract and selected tech contracts.
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
2. Determine whether the change is code-only, spec-only, or contract-affecting.
3. Edit only the required files.
4. Update output_files or relevant specs when the change affects the plan.
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

Only create or update missing structural files such as workspace/.gitignore.
Do not move, delete, rewrite, or untrack existing user files without approval.
```

## 8. publish docs

Publish Markdown specs as an offline HTML site.

```bash
python shiki/tools-skills/skills/spec-to-html/scripts/publish_docs.py <input-path> --title "Shiki Spec" --fail-on-broken-links
```

## 9. publish pretty Shiki spec

Generate an L0 human-friendly spec site from Shiki L1 consensus specs.

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --title "Shiki Spec" --fail-on-broken-links
```

For one feature:

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --feature <TASKID> --title "<TASKID> Spec" --fail-on-broken-links
```
