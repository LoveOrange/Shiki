# Entrance Analysis Workflow

> Role: Scanner. Analyze existing code entries, trace call chains, and write baseline module specs.

## Load

- `shiki_context/project/architecture.md`
- `shiki_context/project/ubiquitous_language.md`
- `shiki_context/modules/[module]/index.md` when present
- target source file from the Init plan

## Steps

1. Infer Method, endpoint, request, response, and purpose from the entry source.
2. Trace Controller/Listener/Job -> Service -> Domain -> Repository/Support calls.
3. Audit architecture violations against generic and selected tech-contract rules.
4. Extract meaningful business concepts without translating field names mechanically.
5. Collect Discovery Log entries for dependencies, external systems, MQ, tables, and caches.

## Output

- Create or update `shiki_context/modules/[module]/entrances/[entrance].md`.
- Create or update `shiki_context/modules/[module]/flows/[scenario].md`.
- Append to `shiki_context/modules/[module]/index.md`.
- Append new concepts to `shiki_context/project/ubiquitous_language.md`.

## Verification

1. Module index is appended, not overwritten.
2. Concept extraction is deduplicated.
3. Flow output contains a tagged Discovery Log.
