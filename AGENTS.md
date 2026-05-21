# Shiki Agent Maintenance Guide

This file is for AI agents maintaining the Shiki repository itself.

## Rules

- Work inside this repository unless the user explicitly asks otherwise.
- Keep framework files generic. Consumer-project facts belong in `shiki_context/` after init.
- When changing workflows, task contracts, templates, tests, or runtime helpers, explain how the change was verified.
- Do not restore, delete, or overwrite unrelated user work.
- Do not store command logs or one-off conclusions in long-lived test specs.

## Regression

The integration regression spec is `tests/SHIKI_FLOW_TESTS.md`.

For small changes, run:

```bash
python3 tools-skills/scripts/verify.py
```

For workflow, task-contract, context-loading, or gate changes, also read
`tests/SHIKI_FLOW_TESTS.md` and check the affected scenarios manually.
