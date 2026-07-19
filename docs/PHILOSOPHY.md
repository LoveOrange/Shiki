# Shiki Philosophy

Shiki does not replace capable coding agents. It gives them a smaller,
deterministic, and recoverable job.

## Files are the collaboration memory

Briefs, current leaf specs, Plans, Task Contracts, tech rules, and output files
form the project skeleton. A fresh provider session can resume from these files
without depending on hidden chat history.

## The Kernel owns coordination

The Kernel selects the next Task, validates dependencies, resolves its Canonical
Contract, builds a deduplicated Context Envelope, and records outputs. A provider
may read, edit, test, and fix only inside that prepared boundary.

The Plan row remains the atomic ledger unit. Provider capability never changes
the Task boundary or merges several Tasks into one completion record.

## Collaboration has two valid shapes

Automatic CLI collaboration favors isolation and repeatability: every Task and
Review receives a fresh Provider session. Manual Prompt collaboration favors
developer continuity: one Task runs in the current Coding Agent session and
Review is explicit.

Neither track is a fallback for the other. They are equal interfaces over the
same deterministic Kernel.

## Specs and tech contracts

Current L1/L2 specs are both model context and a human-readable architecture
map. DDD is the default reference stack because its boundaries help constrain
context, but the Core Kernel is language- and architecture-neutral. Project
teams replace behavior through `shiki_context/constitution/tech_contracts/`.

Shiki's differentiation is deterministic execution: current valid specs,
atomic Task Contracts, minimal Context Envelopes, provider boundaries, and
output-controlled state transitions.
