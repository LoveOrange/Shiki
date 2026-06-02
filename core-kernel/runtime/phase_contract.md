# Phase Contract

This document is fallback guidance. Normal execution routes through `_plan.md`,
`execution_session.md`, a task contract, and a workflow.

## Phase 0: Init

Goal: scan the repository and establish the baseline.

Exit gate:

| file | path | condition |
| :--- | :--- | :--- |
| architecture | `shiki_context/project/architecture.md` | module inventory is present |
| ubiquitous language | `shiki_context/project/ubiquitous_language.md` | at least one concept exists when known |
| scan queue | `shiki_context/workspace/_plan.md` | init.entrance tasks and init.sync are registered |

## Phase 1: Requirement

Goal: clarify human intent and create a feature input.

Exit gate:

| file | path | condition |
| :--- | :--- | :--- |
| design brief | `features/{feature}/design_brief.md` | required sections are filled or marked N/A |
| bootstrap plan | `features/{feature}/_plan.md` | design_init item exists |

## Phase 2: Design

Goal: produce directly implementable L2 AS-IS specs from the design brief.

Exit gate:

| file | path | condition |
| :--- | :--- | :--- |
| feature plan | `features/{feature}/_plan.md` | expanded Target Outputs table exists |
| L2 implementation specs | `features/{feature}/modules/{module}/...` | leaf specs needed by the current Code item exist and are indexed |

Gate to Code:

- Required L2 leaf specs for the current Code item exist.
- Feature `index.md` can route to those leaf specs.
- Downstream Code/Test items are not marked `STALE`.
- Design phase review has passed or the coordinator stopped for human review.

## Phase 3: Code

Goal: implement code from current L2 AS-IS specs.

Entry gate:

- Design gate passed.
- Current Code workflow loaded the related L2 specs, target source, and direct source dependencies.
- Spec-code alignment check was performed before editing.

Exit gate:

| file | path | condition |
| :--- | :--- | :--- |
| implementation | source tree | current L2 AS-IS targets are implemented |
| plan | `features/{feature}/_plan.md` | Code item output_files are filled |

Gate to Test/Merge:

- Code item output_files are filled.
- No output_files entry is marked `STALE`.
- Spec-code drift/alignment has been checked.
- Code item review gates and verification passed.

## Phase 4: Test

Goal: verify implementation, tests, specs, and business expectations.

Exit gate:

- relevant test command or manual verification passed
- no unresolved CHANGE_REQUEST remains
- code/spec drift has been checked

## Phase 5: Merge

Goal: merge feature overlay specs back into baseline.

Exit gate:

| file | path | condition |
| :--- | :--- | :--- |
| baseline specs | `modules/{module}/...` | accepted overlay specs are merged |

## Phase Enum

Use this enum for the `stage` field in `active_task.md`:

```text
Init | Requirement | Design | Code | Test | Merge
```
