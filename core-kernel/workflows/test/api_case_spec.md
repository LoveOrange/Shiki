# API Case Spec

> Role: Test Designer. Write API-level black-box integration cases from the
> entrance/API spec and L2 specs. Do not load source code.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/tests/test_cases.md`
- `features/{feature}/modules/{module}/entrances/*.md`
- `features/{feature}/modules/{module}/flows/*.md`
- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/modules/{module}/designs/acl.md` when present
- `core-kernel/templates/feature/tests/test_cases.md`

## Steps

1. Confirm entrance/API and flow specs exist, otherwise return `BLOCKED`.
2. Do not load target source, controllers, services, repositories, or test code.
3. Extract P0 cases from API path/entry, method, input, auth, business rules,
   error paths, and boundaries.
4. Maintain cases under `Integration Tests` in `tests/test_cases.md`.
5. Each case records scenario name, API, method, description, request, expected
   response, and Gherkin Given/When/Then.
6. Cover happy, bad, and edge behavior. If a required expectation is missing,
   return `CHANGE_REQUEST: test -> spec` instead of inventing it.

## Output

- Update `features/{feature}/tests/test_cases.md`.

## Verification

1. `Integration Tests` exists.
2. Every `TC-INT-*` contains API, method, description, request, expected
   response, and Gherkin.
3. Cases do not reference implementation details.
4. The file does not record execution logs, screenshots, or one-off results.
