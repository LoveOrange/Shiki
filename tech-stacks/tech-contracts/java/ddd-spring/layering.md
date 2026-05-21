# Layering Contract: Java DDD Spring

Root package: `com.example.shop`

```text
adapter/[module]/web|listener        -> REST controllers and message consumers
application/[module]/api/dto         -> DTOs
application/[module]/api/converter   -> DTO assemblers
application/[module]/service         -> application services and transactions
application/[module]/support         -> application-level support interfaces
domain/[module]/model                -> framework-free entities and value objects
domain/[module]/factory              -> domain factories
domain/[module]/service              -> domain services
domain/[module]/repository           -> repository interfaces
domain/[module]/support              -> domain support interfaces
infrastructure/common                -> AppException, ErrorCode, shared utilities
infrastructure/client                -> external SDK clients
infrastructure/[module]/supportimpl  -> Support implementations
infrastructure/[module]/persistence  -> PO, converter, mapper, RepositoryImpl
```

## Dependency Rules

- Domain does not depend on application, adapter, or infrastructure.
- Application depends on domain and injected interfaces, not infrastructure implementations.
- Infrastructure implements domain/application interfaces.
- Entities do not use persistence, serialization, or framework annotations.
