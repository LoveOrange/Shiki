---
name: pretty-shiki-spec
description: Generate a Shiki-specific L0 human-friendly HTML spec from L1 consensus specs.
---

# pretty-shiki-spec

Use this skill when the user asks for a prettier Shiki spec site, a human
review view of Shiki specs, or an L0 spec generated from L1 consensus specs.

## Workflow

1. Identify the Shiki input path. If no path is given and `shiki_context/`
   exists, use it.
2. Use `--feature <id>` when the user wants one feature workspace only.
3. Run `tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py`
   with a clear title.
4. Use `--fail-on-broken-links` when the output is meant for review.
5. Report the generated output directory, missing L1 targets, and broken links.

## Shiki Layers

- L0 is the generated human-friendly review projection.
- L1 is the consensus spec layer: `_plan.md`, `index.md`, leaf specs,
  `tests/test_cases.md`, and `code_contract.md`.
- L2 is standards and loadouts such as workflows and tech contracts. L2 should
  be cited through L1 references instead of duplicated into L0.

## Rules

- Do not modify source L1 Markdown while publishing.
- If L0 and L1 disagree, trust L1 and regenerate after fixing L1.
- Keep generated assets under the requested output directory.
- Do not treat L0 as a coding contract. Coder agents still follow L1 specs.
