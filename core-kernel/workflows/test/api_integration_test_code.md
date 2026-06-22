# API Integration Test Code

> Role: Coder. Write or update API integration test code from Integration Tests
> cases.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/tests/test_cases.md`
- `features/{feature}/modules/{module}/entrances/*.md`
- adapter/API entry source files
- existing integration test directories and bootstrapping conventions
- tech contract: test framework and integration test conventions

## Steps

1. Confirm `Integration Tests` has automatable `TC-INT-*` cases, otherwise
   return `BLOCKED`.
2. Locate the API entrypoint and existing project integration test style.
3. Follow existing MockMvc/WebTestClient/Testcontainers/WireMock or equivalent
   conventions.
4. Assert request method, inputs, status, response fields, and declared
   observable side effects.
5. Do not assert private implementation details or repository internals.
6. Update the current item `output_files` in `_plan.md`.

## Verification

1. Integration test files were created or updated.
2. Tests map to the relevant Integration Tests cases.
3. Assertions depend only on API-observable behavior.
4. Test data setup follows existing project conventions.
