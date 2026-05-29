# Shiki Blueprint

## North Star

Shiki is a workflow kernel for controllable AI software development. Its purpose
is to make AI coding depend less on long chat memory and more on explicit
engineering files:

- bounded phases
- atomic tasks
- minimal context loading
- rule-pack-driven behavior
- file-backed state
- repeatable verification

The kernel should be language-neutral. Languages, architecture styles, model
providers, and private team standards should attach through configuration and
tech contracts rather than being hard-coded into core.

## Product Thesis

Most AI coding failures are workflow failures before they are model failures.
Shiki narrows the model's task. The harness owns decomposition, context assembly,
state transitions, and validation. The stable atom is the bounded plan item and
its task contract; capable runners may execute several safe atoms in one explicit
batch without weakening that ledger.

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

### 6. Verification Gates Are Mandatory

An output is not done because the model replied. It is done when declared
checks pass and plan output is recorded.

### 7. Human Control Stays Visible

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
