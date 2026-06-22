# Shiki Design Contract

This document is mandatory for Design tasks. It prevents a feature overlay from
inventing new concepts when an existing baseline fact can be reused, extended,
or modified.

## Scope

Applies to:

- `design_init`
- `model`
- `persistence`
- `acl`
- `component`
- `entrance_spec`
- `flow`
- `code_contract`

## Reuse Gate

Every Design task must complete this gate before creating or updating its target
artifact.

1. Scope Slice
   - Extract only the part of the design brief or upstream spec owned by the
     current task.
   - Do not turn one task into a full redesign.
   - Return `MANUAL_DECISION` when the task boundary is ambiguous.

2. Reuse Inventory
   - List the baseline specs, source evidence, entrypoints, core classes, or
     upstream design rows that were checked.
   - Identify existing concepts, models, fields, states, entrances, flows,
     services, repositories, supports, and error codes that can carry the new
     requirement.
   - Do not write `add` before checking the relevant baseline or source
     evidence.

3. Minimal Decision
   - Prefer `reuse`, `extend`, or `modify` for each requirement fact handled by
     the current task.
   - Use `add` only when the brief or upstream spec requires it and no equivalent
     baseline/source fact can carry it.
   - Do not add concepts, fields, services, flows, interfaces, or error codes
     for future flexibility.

4. Add Justification
   - Every `add` must name the source fact and explain why reuse or extension is
     not correct.
   - Return `MANUAL_DECISION` when the need for a new fact cannot be proven.

5. Completion Evidence
   - Feature overlay specs must record this gate in `§0 Reuse Decision Gate`.
   - `design_init` must explain why the expanded plan includes only the affected
     items.
   - `code_contract.md` extracts implementable facts from L2 specs; it does not
     create new design facts.

## Forbidden

- Adding business concepts, models, flows, entrances, services, fields, states,
  or error codes without brief or upstream spec evidence.
- Replacing a missing or incomplete baseline with an idealized full snapshot.
- Copying the whole baseline into a feature overlay to hide uncertainty.
- Recording uncertain reuse/add decisions as confirmed current facts.
- Adding future extension points or generic abstractions for one feature.
