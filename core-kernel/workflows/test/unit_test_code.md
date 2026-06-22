# Unit Test Code

> Role: Coder. Write or update unit test code from Unit Tests cases.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/tests/test_cases.md`
- target source files
- existing test directories, base classes, and naming conventions
- tech contract: test framework, mock conventions, and layering rules

## Steps

1. Confirm `Unit Tests` has automatable `TC-UNIT-*` cases, otherwise return
   `BLOCKED`.
2. Locate target class and methods; load only target source, direct dependencies,
   and necessary test examples.
3. Follow existing JUnit/Mockito/AssertJ or equivalent project conventions.
4. Unit tests must not start the full application; third-party dependencies use
   mocks, stubs, or fakes.
5. Each new or updated test method should trace to a `TC-UNIT-*` case.
6. Update the current item `output_files` in `_plan.md`.

## Verification

1. Test files were created or updated.
2. Unit tests map to the relevant Unit Tests cases.
3. Mock boundaries match test case Input/Expected.
4. No unrelated integration-test startup cost is introduced.
