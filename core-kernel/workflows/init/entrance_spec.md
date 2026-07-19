# Entrance Spec Workflow

Generate or update one baseline entrance aggregate from the selected Plan item.

## Steps

1. Require a target under `modules/{module}/entrances/`; a missing target file is a create case.
2. Extract name, purpose, method/URL/trigger, request, response, authorization, validation, errors, idempotency, and compatibility from evidence.
3. Keep implementation class and method names in source references.
4. One entrance file may aggregate several endpoints while preserving addressable sections.
5. Create a minimal module index from the template when missing; do not invent module responsibilities.
6. Add or update the index route for the entrance.
7. Record only the primary entrance spec in the Plan item's `output_files`.

## Verification

- The entrance does not duplicate a complete Service/Repository call chain.
- Authorization, errors, request, and response facts have evidence.
- The module index resolves the entrance file.
