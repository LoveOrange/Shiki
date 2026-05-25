# Naming Contract: Python Default

## Modules And Packages

- Use lowercase package and module names.
- Use underscores for multi-word module names, for example `order_service.py`.
- Keep package names stable and domain-oriented; do not encode temporary delivery details.
- Public modules should expose a small, intentional API through clear function, class, or service names.

## Symbols

| symbol | style | example |
| :--- | :--- | :--- |
| package/module | `snake_case` | `order_service` |
| function/method | `snake_case` | `create_order` |
| variable/attribute | `snake_case` | `order_id` |
| class | `PascalCase` | `OrderService` |
| exception class | `PascalCase` + `Error` | `OrderNotFoundError` |
| constant | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| type alias | `PascalCase` | `OrderId` |

## File Placement

- Keep production code under the configured source root, commonly `src/<package>/`.
- Keep tests under `tests/` with names matching `test_*.py`.
- Keep command-line entrypoints thin; move business logic into importable modules.
