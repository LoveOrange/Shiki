# Shiki Blueprint

## North Star

Shiki is a workflow kernel for controllable AI software development. Its purpose
is to make AI coding depend less on long chat memory and more on explicit
engineering files:

- bounded phases
- atomic tasks
- adaptive execution sessions
- minimal context loading
- rule-pack-driven behavior
- file-backed state
- repeatable verification

The kernel sits above provider-local coding loops. Providers may read, edit,
test, and fix inside a bounded assignment; Shiki owns the project and phase loop
that chooses the assignment, loads context, applies gates, records evidence, and
preserves resumable state.

The kernel should be language-neutral. Languages, architecture styles, model
providers, and private team standards should attach through configuration and
tech contracts rather than being hard-coded into core.

## Product Thesis

Most AI coding failures are workflow failures before they are model failures.
Shiki narrows the model's task. The harness owns decomposition, context
assembly, topology selection, state transitions, review gates, and validation.
The stable atom is the bounded plan item and its task contract; capable runners
may execute several safe atoms inside one adaptive execution session without
weakening that ledger.

Shiki specs are also the technical project skeleton. They should help models
write code, but they should also let technical users inspect module boundaries,
domain language, flows, interfaces, persistence decisions, integration points,
risks, and verification evidence without reverse-engineering the whole source
tree.

## Design Principles

### 1. Phase Machine Over Chat Flow

The project advances through explicit phases instead of an open-ended
conversation:

```text
Init -> Requirement -> Design -> Code -> Test -> Merge
```

### 2. Files Over Conversation Memory

Long-lived knowledge must be stored as files. A new model session should be able
to resume from repository state without hidden chat history.

### 3. Task Contracts Over Prompt Templates

Prompts are implementation details. The stable unit is the task contract: goal,
inputs, references, output, checks, retry policy, and done condition.

### 4. Tech Contracts As Replaceable Loadouts

The kernel must not know what Java, Spring, React, pytest, or any private rule
set means. Those belong in stack ids such as `java/ddd-spring`.

### 5. Runners Are Adapters

Shiki starts with command-oriented integration because it is portable. Future
runners can support provider SDKs, local model servers, hosted execution, or IDE
agents without changing task contracts.

### 6. DDD Is The Reference Stack, Not The Kernel

DDD is Shiki's default architecture stance because bounded contexts,
ubiquitous language, aggregates, domain services, repositories, adapters, and
ACLs give agents business-aligned boundaries. Those boundaries make product
intent easier to trace into implementation.

Core Kernel must not assume DDD concepts directly. It should understand phase,
plan item, task contract, workflow, tech contract, leaf spec, evidence, and
gates. DDD, MVC, frontend, data-pipeline, or private architecture styles should
be replaceable through tech contracts and templates.

### 7. Phase Orchestrators Loop Over Task Primitives

`next` is the primitive execution step. Higher-level phase commands such as
future `arch` or `coding` commands should orchestrate repeated `next`-style
execution until a phase gate, blocker, manual decision, failed verification,
context budget, or configured review/fix policy stops the run.

Auto-review and auto-fix modes strengthen the loop by adding deeper review and
bounded retries. They must not bypass mandatory acceptance gates or mark a plan
item done without evidence and verification.

### 8. Verification Gates Are Mandatory

An output is not done because the model replied. It is done when declared
checks pass, review passes, evidence is recorded, and plan state is updated.

### 9. Tool Topology Is Internal

Users should not choose single-agent or agent-team mode. Shiki detects adapter
capabilities and chooses the execution topology internally from plan graph,
context budget, risk, and stop conditions.

### 10. Human Control Stays Visible

Humans can edit briefs, override tech contracts, retry tasks, mark gates blocked,
accept or reject design, and merge or discard feature overlays.

## First Public Milestone

The first public milestone is a small but complete loop:

```text
Design Brief -> L2 AS-IS Specs -> Code Task -> Verification Gate
```

Required outcomes:

- one task contract format
- one command runner boundary
- one reference tech contract stack
- one example project
- one verification script that checks more than file existence
