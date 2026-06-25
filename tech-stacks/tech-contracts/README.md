# Tech Contracts

`tech-contracts/` stores replaceable stack rules. Shiki provides defaults under
`shiki/tech-stacks/tech-contracts/`; init copies selected stacks into
`shiki_context/constitution/tech_contracts/` for project ownership.

DDD is the default reference architecture because it gives agents
business-aligned boundaries and a stable vocabulary for product-to-code
traceability. It is not a Core Kernel assumption. Projects can replace the
architecture style by selecting or authoring another tech contract stack.

## Loading Rules

| stack id | project copy | purpose |
| :--- | :--- | :--- |
| `java/ddd-spring` | `shiki_context/constitution/tech_contracts/java/ddd-spring/` | Java DDD + Spring layered architecture |
| `python/default` | `shiki_context/constitution/tech_contracts/python/default/` | Framework-neutral Python application rules |
| `shiki-core` | `shiki_context/constitution/tech_contracts/shiki-core/` | Shiki framework maintenance rules |

Workflows reference slices on demand:

```markdown
## Load
- tech contract: `shiki_context/constitution/tech_contracts/<stack_name>/naming.md`
```

## Suggested Structure

| file | content |
| :--- | :--- |
| `naming.md` | suffixes, path names, table names |
| `layering.md` | layer/package rules and dependency direction |
| `exception.md` | exception and error-code policy |
| `persistence.md` | storage and mapping rules |
| `acl.md` | anti-corruption layer rules |
| `testing.md` | test layout, fixtures, and verification rules |

New stacks should use hierarchical ids such as `typescript/nextjs`,
`python/default`, `python/fastapi`, or `go/clean-architecture`.
