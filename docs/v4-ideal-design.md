# Shiki v4 Ideal Design

Shiki v4 separates deterministic workflow truth from collaboration style.

The Core Kernel is the only authority for selecting a Task, resolving its
Contract, assembling context, validating dependencies, and recording outputs.
User interfaces decide only how that prepared Task reaches a Provider.

The ideal design has these invariants:

1. A Plan row is one atomic Task.
2. Canonical Contracts contain full behavior; Alias Contracts contain only an
   id and Canonical reference.
3. The Context Envelope is complete, ordered, and content-deduplicated.
4. `output_files` is the completion ledger.
5. Task failure and Review results are returned by the session and are not Plan
   columns.
6. CLI and Prompt tracks share Kernel tools but have distinct session ownership.
7. Optional Flow specifications are created only when the Plan explicitly asks
   for them.

This makes Prompt files disposable interfaces rather than a second workflow
engine, while keeping automatic CLI execution reproducible across Providers.
