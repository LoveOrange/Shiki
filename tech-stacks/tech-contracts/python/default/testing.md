# Testing Contract: Python Default

## Test Shape

- Use `pytest` when the project already uses it; otherwise keep tests compatible with standard `unittest`.
- Name test files `test_*.py`.
- Test behavior through public functions, services, or ports instead of private implementation details.
- Keep domain tests independent from databases, networks, clocks, and environment variables.

## Fixtures And Fakes

- Use small fixtures close to the tests that need them.
- Prefer fakes for ports over mocking deep call chains.
- Keep integration tests clearly separated when they require real infrastructure.

## Verification

- Run the smallest relevant test target after a change.
- Run formatting, linting, type checking, or import checks when the project declares those tools.
- If a check cannot run, record the missing tool, dependency, or environment requirement.
