# Sync Project Artifact Workflow

Synchronize one project-level baseline artifact selected by the current Init Plan target.

## Steps

1. Select the concern from the target: architecture, integration, ubiquitous language, tech stack, tech debt, or project index.
2. Load only evidence needed by that target.
3. Merge evidence into existing content without inventing or duplicating facts.
4. Create or update only the selected project artifact body.
5. Record that artifact's full `shiki_context/... ` path in `output_files`.

## Verification

- The target file exists.
- Every new fact traces to completed Init output, configuration, or source evidence.
- Index files contain routing, not task state or detailed spec content.
