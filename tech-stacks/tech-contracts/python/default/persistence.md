# Persistence Contract: Python Default

## Data Access

- Keep persistence code under `infrastructure/` or another clearly named adapter package.
- Repository ports expose domain types, not ORM models, SQL rows, SDK DTOs, or JSON dictionaries.
- Repository implementations perform mapping inside the repository layer.
- Keep transactions at the application or unit-of-work boundary.

## Mapping Rules

- Use dataclasses, typed classes, or framework models intentionally; do not pass untyped dictionaries across layers when the shape is stable.
- Keep serialization, validation, and persistence annotations out of domain objects unless the project explicitly chooses an active-record style.
- Convert timestamps, decimals, identifiers, and enums at the boundary so domain code receives domain-friendly types.

## IO Rules

- Make filesystem, network, database, and clock access injectable for business logic.
- Avoid module-import side effects that connect to services, read files, or mutate process state.
- Close files, sessions, cursors, clients, and temporary resources deterministically.
