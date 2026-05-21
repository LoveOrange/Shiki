# Exception Contract: Java DDD Spring

Default classes:

- `com.example.shop.infrastructure.common.exception.AppException`
- `com.example.shop.infrastructure.common.exception.ErrorCode`

Domain and application layers throw business exceptions:

```java
throw new AppException(ErrorCode.ORDER_NOT_FOUND);
```

Infrastructure translates technical or external exceptions:

```java
try {
    externalClient.call();
} catch (SdkException e) {
    throw new AppException(ErrorCode.SYSTEM_ERROR, "external call failed", e);
}
```

Do not leak `SQLException`, `RedisException`, SDK exceptions, or transport
exceptions above infrastructure boundaries.
