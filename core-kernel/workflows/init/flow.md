# Init Flow Workflow

Generate or update one optional baseline scenario flow with a core sequence diagram.

## Steps

1. Require a target under `modules/{module}/flows/`.
2. Reference the relevant entrance section without duplicating complete request/response definitions.
3. Trace the actual scenario from entrance through service, domain, repository, and support components.
4. Record business steps, state changes, transaction boundary, side effects, and error paths.
5. Use only participants and calls supported by source or current specs.
6. Update the flow and its module index route.
7. Record only the primary flow spec in `output_files`.

## Verification

- The flow references an entrance and contains a `sequenceDiagram`.
- Participants match current source or specs.
- Discovery findings are recorded or explicitly absent.
