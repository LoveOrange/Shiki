# Run And Route Tests

> Role: Reviewer. Run the project test command or verifier and classify failures
> before routing them.

## Load

- `features/{feature}/_plan.md`
- `features/{feature}/tests/test_cases.md`
- current feature test files
- project test command or verifier convention

## Steps

1. Confirm relevant unit or integration test code items have `output_files`;
   return `BLOCKED` if they do not.
2. Run the smallest relevant project test command or verifier.
3. If it passes, record the command/evidence summary in the current item
   `output_files` or evidence column.
4. If it fails, classify before proposing a fix:
   - current specs are correct but implementation differs:
     `CHANGE_REQUEST: test -> code`
   - test reveals missing acceptance/spec detail:
     `CHANGE_REQUEST: test -> spec`
   - business rules conflict or feature goals are incompatible:
     `CHANGE_REQUEST: test -> feature`
5. Do not mark this item complete when tests fail. Do not default to a code
   hotfix before classifying the route.

## Verification

1. Passing runs have clear command or verifier evidence.
2. Failing runs have a route classification and next action.
3. Execution logs are not written into `tests/test_cases.md`.
