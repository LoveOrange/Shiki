# Discovery Sync Workflow

> Role: Scanner. Aggregate module-local Discovery Logs into project-level architecture and tech debt.

## Load

- all `shiki_context/modules/*/flows/*.md` files
- `shiki_context/project/architecture.md`
- `shiki_context/project/integration.md`
- `shiki_context/project/tech_debt.md` when present

## Steps

1. Scan flow files for Discovery Log and architecture audit entries.
2. Extract cross-module dependencies.
3. Extract MQ topics and external systems.
4. Collect architecture violations and warnings.
5. Deduplicate findings while preserving source references.

## Output

- Update `shiki_context/project/architecture.md` dependency summary.
- Update `shiki_context/project/integration.md` external and MQ summaries.
- Create or update `shiki_context/project/tech_debt.md`.

## Verification

1. Cross-module dependencies are aggregated when present.
2. Tech debt file exists when violations are found.
3. Module-local detail is not duplicated unnecessarily.
