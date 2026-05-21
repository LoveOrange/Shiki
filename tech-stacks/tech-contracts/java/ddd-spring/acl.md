# ACL Contract: Java DDD Spring

## Support Interfaces

- Location: `domain/[module]/support/` or `application/[module]/support/`.
- Name: `XxxSupport`.
- Signatures may use Entity, VO, and primitive types only.
- External DTOs must not appear in Support signatures.

## Support Implementations

- Location: `infrastructure/[module]/supportimpl/`.
- Name: `XxxSupportImpl`.
- Responsibilities:
  1. Convert domain input to external DTOs.
  2. Call external clients or SDKs.
  3. Convert external responses back to domain types.
  4. Translate external exceptions into `AppException`.

```text
App/Domain Service -> Entity/VO -> Support interface
                                      |
                                      v
                              SupportImpl -> ExternalDTO -> Client/SDK
```
