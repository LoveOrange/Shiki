# ACL Design

> Role: Architect. Produce module boundary and anti-corruption design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/design_brief.md`
- tech contract: ACL

## Steps

1. Confirm model design exists.
2. Define business boundary, internal dependencies, external dependencies, and Support interfaces.
3. Use only Entity, VO, or primitive types in Support signatures.
4. Add dependency topology.
5. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/acl.md`

## Verification

1. Output file exists.
2. Support signatures contain no DTOs.
3. Dependency direction is valid.
4. No implementation code is present.
