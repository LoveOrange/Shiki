# Phase Contract

This document is fallback guidance. Normal execution routes through `_plan.md`, a
task contract, and a workflow.

## Phase 0: Init

Goal: scan the repository and establish the baseline.

Exit gate:

| artifact | path | condition |
| :--- | :--- | :--- |
| architecture | `shiki_context/project/architecture.md` | module inventory is present |
| ubiquitous language | `shiki_context/project/ubiquitous_language.md` | at least one concept exists when known |
| scan queue | `shiki_context/workspace/_plan.md` | init.entrance tasks and init.sync are registered |

## Phase 1: Requirement

Goal: clarify human intent and create a feature input.

Exit gate:

| artifact | path | condition |
| :--- | :--- | :--- |
| design brief | `features/{feature}/design_brief.md` | required sections are filled or marked N/A |
| bootstrap plan | `features/{feature}/_plan.md` | design_init item exists |

## Phase 2: Design

Goal: produce design artifacts and converge them into a code contract.

Exit gate:

| artifact | path | condition |
| :--- | :--- | :--- |
| feature plan | `features/{feature}/_plan.md` | expanded target artifact table exists |
| code contract | `features/{feature}/code_contract.md` | sections 1-6 are non-empty, confirmations checked, version set |

## Phase 3: Code

Goal: implement code from the code contract.

Entry gate:

- Design gate passed.
- `code_contract.md` exists and is confirmed.

Exit gate:

| artifact | path | condition |
| :--- | :--- | :--- |
| implementation | source tree | declared targets are implemented |
| plan | `features/{feature}/_plan.md` | Code item output_files are filled |

## Phase 4: Test

Goal: verify implementation, tests, specs, and business expectations.

Exit gate:

- relevant test command or manual verification passed
- no unresolved CHANGE_REQUEST remains
- code/spec drift has been checked

## Phase 5: Merge

Goal: merge feature overlay specs back into baseline.

Exit gate:

| artifact | path | condition |
| :--- | :--- | :--- |
| baseline specs | `modules/{module}/...` | accepted overlay specs are merged |

## Phase Enum

Use this enum for the `stage` field in `active_task.md`:

```text
Init | Requirement | Design | Code | Test | Merge
```
