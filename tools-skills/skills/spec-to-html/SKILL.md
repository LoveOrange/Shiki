---
name: spec-to-html
description: Convert Markdown specs or directories into an offline HTML documentation site.
---

# spec-to-html

Use this skill when the user asks to publish Markdown specs as HTML or a local
web spec site.

## Workflow

1. Identify the input path. If no path is given and `shiki_context/` exists, use it.
2. Run `tools-skills/skills/spec-to-html/scripts/publish_docs.py` with a clear title.
3. Use `--fail-on-broken-links` when the output is meant for review.
4. Report the generated output directory and any broken links.

## Rules

- Do not assume the input is a Shiki project.
- Do not modify source Markdown while publishing.
- Keep generated assets under the requested output directory.
