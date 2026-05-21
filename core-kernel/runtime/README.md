# Runtime

Runtime documents define how Shiki loads context, routes task contracts, and
checks phase gates. Normal execution flows through:

```text
active_task.md -> _plan.md -> task contract -> workflow -> template/tech contract
```

Use `phase_contract.md` only as fallback guidance when plan or gate state is
missing. Use `context_loading.md` as the authoritative loading policy.
