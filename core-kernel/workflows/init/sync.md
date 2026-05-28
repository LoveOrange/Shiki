# Discovery Sync Workflow

> Role: Scanner. Aggregate module-local Discovery Logs into project-level architecture and tech debt.

## Load

- `shiki_context/workspace/_plan.md`
- `shiki_context/project/index.md`
- module indexes that list completed flows
- `shiki_context/project/architecture.md`
- `shiki_context/project/integration.md`
- `shiki_context/project/tech_debt.md` when present

Do not load every `shiki_context/modules/*/flows/*.md` body at once. When there
are many flows, process by module or flow batch and read only Discovery Log or
architecture-audit snippets.

## Steps

1. Build the completed flow list from workspace plan output files and module indexes.
2. Scan only the relevant flow snippets for Discovery Log and architecture audit entries.
3. Extract cross-module dependencies.
4. Extract MQ topics and external systems.
5. Collect architecture violations and warnings.
6. Deduplicate findings while preserving source references.

## Output

- Update `shiki_context/project/architecture.md` dependency summary.
- Update `shiki_context/project/integration.md` external and MQ summaries.
- Create or update `shiki_context/project/tech_debt.md`.

## Verification

1. Cross-module dependencies are aggregated when present.
2. Tech debt file exists when violations are found.
3. Module-local detail is not duplicated unnecessarily.
