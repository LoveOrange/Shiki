# Layering Contract: Python Default

This stack is framework-neutral. Apply the same dependency direction whether the
project is a package, service, CLI, worker, or automation.

```text
interfaces/ or api/      -> HTTP, CLI, event, or job entrypoints
application/             -> use cases, orchestration, transactions
domain/                  -> framework-free entities, value objects, policies
ports/                   -> repository, gateway, or client interfaces
infrastructure/          -> database, filesystem, network, SDK implementations
```

## Dependency Rules

- Domain code does not import interface, application, or infrastructure modules.
- Application code depends on domain objects and ports, not concrete infrastructure.
- Infrastructure implements ports and translates external data into domain types.
- Interface code validates transport input and calls application services.
- Keep framework decorators, request objects, ORM models, SDK clients, and environment lookups out of domain code.

## Module Boundaries

- Prefer explicit constructor or function parameters over reading globals inside business logic.
- Keep side effects at entrypoint, infrastructure, or application boundaries.
- Do not hide cross-module calls behind broad utility modules; name the port or service by its business role.
