# ACL Design

> Role: Architect. Produce module boundary and anti-corruption design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/design_brief.md`
- baseline `modules/{module}/designs/acl.md` when present and read-only
- tech contract: ACL

## Steps

1. Confirm model design exists.
2. Define business boundary, module dependencies, external dependencies, and Support interfaces.
3. For feature overlays, compare baseline ACL when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
4. Use only Entity, VO, or primitive types in Support signatures.
5. Add dependency topology.
6. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/acl.md`

## Verification

1. Output file exists.
2. Support signatures contain no DTOs.
3. Dependency direction is valid.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. No implementation code is present.
