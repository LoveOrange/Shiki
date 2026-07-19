# Phase Contract

Fallback guidance only. Normal execution routes through the active Plan, one Task Contract, and its Workflow.

## Init

Goal: establish a project/module baseline from existing source.

Exit when the Init Plan is complete, required project indexes exist, and every recorded baseline fact has source/configuration evidence.

## Design

Goal: produce bounded feature overlay leaf specs from the Design Brief.

Exit when required inputs for the first Code Task exist, the feature index routes them, and brownfield reuse/add decisions have evidence.

## Code

Goal: implement the current L2 specs.

Exit when current Code Task outputs exist and the Workflow's project checks pass. Spec/code drift must be routed explicitly, not hidden in a Review state column.

## Test

Goal: verify implementation, tests, specs, and business expectations.

Exit when applicable test cases and automated tests exist and the selected verifier passes. A failure remains BLOCKED until the developer authorizes a corrective Task.

## Merge

Goal: merge accepted feature overlay facts into baseline.

Exit when accepted overlay specs have been merged and validated.

The `active_task.stage` enum is:

`Init | Design | Code | Test | Merge`
