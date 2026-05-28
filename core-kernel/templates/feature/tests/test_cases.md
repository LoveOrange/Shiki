# Test Cases: [FEAT-ID]

This file records what to verify. Do not store one-off run logs or screenshots here.

## Case Map

- [FEAT-ID]
  - Happy Path
    - TC-001: [scenario]
      - Given: [precondition]
      - When: [action]
      - Then: [expected result]
      - Covers: `modules/{module}/...#[section]`
      - Type: manual | automated | exploratory
      - Priority: P0 | P1 | P2
  - Boundary
  - Error / Exception
  - Permission / Security
  - Idempotency / Concurrency
  - Integration / External Dependency
  - Regression

## Rules

- Each executable case needs a stable id, Given/When/Then, coverage source, type, and priority.
- If a test case conflicts with L2 AS-IS specs, the current valid leaf specs win.
- Execution results belong in local test output or CI, not in this spec.
