# Core Kernel

This module owns Shiki's stable process semantics.

- `runtime/`: context loading, phase gate, and machine-readable task contracts.
- `workflows/`: task execution views for agents and providers.
- `templates/`: context-store scope templates and feature lifecycle templates.
- `_lib/`: shared kernel helpers used by tools.

Core Kernel owns routing, contracts, context loading, workflow binding, evidence, and memory semantics.
