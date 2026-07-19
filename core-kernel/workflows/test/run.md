# Run Tests

> Role: Test Executor. Run project verification for the current feature and report the result; do not select another Task.

## Steps

1. Require relevant unit/integration test-code items to have existing files in `output_files`.
2. Run the smallest project-standard test or verifier command that covers the current scope.
3. Return `PASS: <summary>` on success and report the command and concise evidence.
4. Return `BLOCKED: <reason>` on failure, followed by failure evidence, implementation/spec/requirement classification, and a bounded recommendation.
5. Do not repair the failure, edit the Plan, or select the next Task.

## Verification

- The executed command, exit status, and summary are inspectable.
- Failure classification is evidence-backed.
- Execution logs were not written into `tests/test_cases.md`.
