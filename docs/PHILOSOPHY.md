# Shiki Philosophy

Shiki is a deterministic agent workflow kernel for software delivery. It does
not try to replace coding agents. It gives strong coding agents a smaller,
clearer, and more verifiable job.

## Position

Shiki sits between project-level intent and provider-local coding loops:

```text
product / project goal
-> Shiki phase orchestrator
-> Shiki execution window
-> Codex, Claude Code, OpenCode, Gemini, or another provider
-> source, specs, evidence, and plan state
```

Providers such as Codex and Claude Code already have their own local loop for
reading files, editing code, running tests, and fixing errors. Shiki should not
duplicate that loop. Shiki owns the wider phase loop: which task is next, which
context is loaded, which boundary must not be crossed, when review is required,
how evidence is recorded, and how work resumes from files instead of chat
memory.

## Specs As Project Skeleton

Shiki specs are not only prompt material for code generation. They are the
project skeleton:

- human-readable architecture map for technical users
- model-facing context index for bounded execution
- current valid source of engineering facts
- review and verification basis for plan item completion
- recovery state for a fresh model session

Generated L0 views may make the skeleton easier for humans to review, but the
canonical execution facts stay in current valid L1/L2 specs and plan ledgers.

## DDD By Default

Shiki uses DDD as its reference architecture stack because DDD gives agents a
business-aligned software structure:

- bounded contexts constrain context loading
- ubiquitous language connects product language and code names
- aggregates, entities, value objects, and domain services make business
  responsibility explicit
- repositories, adapters, and ACLs make infrastructure boundaries explicit
- flows and use cases connect user value to implementation paths
- invariants and business rules become review and test inputs

This is a default stack, not a kernel assumption. The Core Kernel only knows
phase, plan item, task contract, workflow, tech contract, leaf spec, evidence,
and gates. Architecture style belongs in replaceable tech contracts.

## Replaceable Tech Contracts

Tech contracts turn architecture style into loadable rules. A DDD stack can map
Shiki design slots to aggregates, repositories, ACLs, and application services.
Another stack can map the same execution concepts to MVC controllers, frontend
routes, data pipelines, or another architecture.

The kernel should stay language-neutral and style-neutral. The default
distribution can be opinionated; project-owned `shiki_context/constitution`
copies are where teams adapt or replace those opinions.

## Granularity

The plan item is the atomic ledger unit. It should remain small enough to review,
verify, retry, and recover.

The execution window is the model-capability unit. A small provider may execute
one item. A stronger provider may execute a bounded sequence of compatible items
inside one session. The ledger does not get merged just because the provider can
handle more context.

## Phase Orchestrators

`next` is the primitive execution step: select a ready item or bounded execution
window, execute it through a task contract, review it, verify it, and update
state only after the gate passes.

Future phase commands such as `arch` and `coding` should be orchestrators over
that primitive. They should loop until a phase gate, blocker, manual decision,
failed verification, context boundary, or configured policy stops the run.

Auto-review and auto-fix modes should strengthen the loop, not weaken it:

```text
execute item
-> mandatory acceptance gate
-> optional deeper review
-> bounded fix retry when review returns a concrete change request
-> evidence and plan update
```

## Relationship To Spec Tools

Shiki can consume external product or spec artifacts. Its differentiation is not
owning a new taxonomy for requirements. Its differentiation is deterministic
execution: current valid specs, atomic task contracts, adaptive execution
windows, provider boundaries, evidence, and gate-controlled state transitions.
