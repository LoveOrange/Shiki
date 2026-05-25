# Exception Contract: Python Default

## Error Types

- Define domain and application exceptions as explicit classes.
- Exception classes use the `Error` suffix.
- Do not raise or catch broad `Exception` unless the boundary must translate unknown failures.
- Do not use exceptions for expected branch control when a typed result is clearer.

```python
class OrderNotFoundError(ApplicationError):
    pass


raise OrderNotFoundError(order_id)
```

## Boundary Translation

- Infrastructure catches library-specific exceptions and raises project exceptions.
- Interface layers translate project exceptions into transport-specific responses or exit codes.
- Domain and application layers must not leak SDK, database, HTTP, filesystem, or framework exceptions.

```python
try:
    return client.fetch_order(order_id)
except ExternalClientError as exc:
    raise OrderGatewayError(order_id) from exc
```

## Diagnostics

- Preserve exception chaining with `raise ... from exc` when translating errors.
- Error messages may include stable identifiers, but must not include secrets, tokens, or credentials.
