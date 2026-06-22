# Test Cases: [FEAT-ID]

This file records what to verify. Do not store one-off run logs or screenshots here.

## Case Map

- [FEAT-ID]
  - Integration Tests
    - TC-INT-001: [scenario]
      - API: [path or entrance name]
      - Method: [GET/POST/PUT/DELETE/...]
      - Description: [case description and covered spec]
      - Request: [path params, query, headers, and body]
      - Expected Response: [status, body, error code, or key fields]
      - Gherkin:
        - Given: [precondition]
        - When: [API call]
        - Then: [expected response or observable result]
  - Unit Tests
    - TC-UNIT-001: [case name]
      - Class: [target class]
      - Method: [target method]
      - Description: [case description]
      - Input: [method args, dependency returns, and required state]
      - Expected: [return value, exception, state change, or mock interaction]

## Rules

- Integration cases do not load source code as input; they are based on
  entrance/API specs and L2 specs.
- Integration cases use `TC-INT-*` and include API, Method, Description,
  Request, Expected Response, and Gherkin Given/When/Then.
- Unit cases use `TC-UNIT-*` and include Class, Method, Description, Input, and
  Expected.
- Unit cases may read target source and direct dependencies; required mock
  behavior belongs in Input or Expected.
- If a test case conflicts with L2 AS-IS specs, the current valid leaf specs win.
- Execution results belong in local test output or CI, not in this spec.
