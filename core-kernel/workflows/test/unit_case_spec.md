# Unit Case Spec

> Role: Test Designer. Write unit test cases from code contract, target source,
> and direct dependencies.


## Steps

1. Confirm target source or code contract is available, otherwise return
   `BLOCKED`.
2. Load only the target class and direct dependencies.
3. Identify target classes, methods, core branches, errors, boundaries, and
   third-party dependency mock behavior.
4. Maintain cases under `Unit Tests` in `tests/test_cases.md`.
5. Each case records class, method, description, input, and expected result.
6. Put required mock behavior in Input or Expected. If the expected behavior is
   unclear, return `CHANGE_REQUEST: test -> spec` or `BLOCKED`.

## Output

- Update `features/{feature}/tests/test_cases.md`.

## Verification

1. `Unit Tests` exists.
2. Every `TC-UNIT-*` contains class, method, description, input, and expected
   result.
3. Mock behavior is expressed in Input or Expected.
4. The file does not record execution logs, screenshots, or one-off results.
