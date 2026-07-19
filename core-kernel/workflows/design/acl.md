# ACL Design

> Role: Architect. Produce module boundary and anti-corruption design only.


## Steps

1. Confirm model design exists.
2. Run the Design Contract Reuse Gate for ACL scope: list checked baseline/source boundaries, dependencies, supports, and external integrations.
3. Define business boundary, module dependencies, external dependencies, and Support interfaces with minimal change.
4. For feature overlays, compare baseline ACL when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
5. Record `§0 Reuse Decision Gate`; each `add` needs source evidence and a reason reuse/extension is not correct.
6. Use only Entity, VO, or primitive types in Support signatures.
7. Add dependency topology.
8. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/acl.md`

## Verification

1. Output file exists.
2. Support signatures contain no DTOs.
3. Dependency direction is valid.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. Reuse Decision Gate records checked candidates and add justification.
6. No implementation code is present.
