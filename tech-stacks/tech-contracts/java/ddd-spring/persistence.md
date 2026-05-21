# Persistence Contract: Java DDD Spring

## Stack Defaults

| dimension | choice |
| :--- | :--- |
| ORM | MyBatis Plus / MyBatis |
| Mapping | MapStruct or manual converter |
| Boilerplate | Lombok allowed when the project uses it |
| Java | JDK 8+ |

## PO Rules

- Put PO classes under `infrastructure/[module]/persistence/po/`.
- PO classes use the `PO` suffix.
- Flatten VO fields into columns.
- `@TableName` appears on PO classes only.
- Entities must not contain persistence annotations.

## Converter Rules

- Entity-to-PO conversion lives under `infrastructure/[module]/persistence/converter/`.
- Repository interfaces use Entity types, not PO types.
- RepositoryImpl performs conversion internally.

## DI Rules

- Prefer constructor injection or `@RequiredArgsConstructor`.
- Do not use field injection with `@Autowired`.
