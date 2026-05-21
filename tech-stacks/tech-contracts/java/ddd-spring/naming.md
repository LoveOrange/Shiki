# Naming Contract: Java DDD Spring

| component | suffix | example |
| :--- | :--- | :--- |
| Entity | none | `Order` |
| Value Object | `VO` | `AddressVO` |
| Factory | `Factory` | `OrderFactory` |
| DTO | `DTO` | `CreateOrderDTO` |
| App Service | `Service` | `OrderService` |
| Domain Service | `DomainService` | `OrderDomainService` |
| Repository interface | `Repository` | `OrderRepository` |
| Mapper | `Mapper` | `OrderMapper` |
| Persistence Object | `PO` | `OrderPO` |
| ACL interface | `Support` | `PaymentSupport` |
| ACL implementation | `SupportImpl` | `PaymentSupportImpl` |

Database table names use `[module]_[entity_lowercase]`, for example `order_coupon`.
