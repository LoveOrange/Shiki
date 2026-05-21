# Shiki

Shiki is a spec-first workflow harness for controllable AI-assisted software development.
It is not a chat assistant, a model provider, or a language framework. It is a small
kernel that turns software work into explicit phases, bounded tasks, file-backed
context, swappable tech contracts, and verifiable gates.

The name comes from Ryougi Shiki. For this project, it marks a clean break from
ad hoc prompt programming: AI coding should run through durable engineering
artifacts instead of hidden conversation memory.

## Why Shiki

AI coding fails most often when the model is asked to infer too much at once:

- intent is vague, so architecture is guessed
- long conversations become fragile state
- large repositories dilute attention
- generated code drifts from team rules
- a reply is treated as done before the artifact is valid

Shiki narrows the model's job. The harness owns task routing, context loading,
state transitions, and validation. The model performs one bounded task against a
contract.

## Core Ideas

- Workflow-driven execution: each task is routed from `_plan.md` to a task contract and a workflow.
- File-backed state: briefs, specs, plans, tech rules, and outputs live in versioned files.
- Current valid specs: the active leaf specs in scope are the source of truth.
- Code contract gate: design artifacts converge into `code_contract.md`; code follows that contract.
- Tech contracts: language and architecture rules are replaceable stacks such as `java/ddd-spring`.
- Minimal context: normal tasks load only plan state, direct dependencies, workflow, templates, and selected tech rules.

## Quick Start

Use Shiki as a read-only submodule or subtree inside a consumer project:

```bash
git submodule add https://github.com/LoveOrange/Shiki.git shiki
python shiki/tools-skills/scripts/init.py
```

Initialization creates:

```text
shiki.config.yaml
shiki_context/
  workspace/
  constitution/tech_contracts/
  project/
  modules/
  features/
```

Create a feature workspace:

```bash
python shiki/tools-skills/scripts/new_feature.py --taskid FEAT-001
```

Then use `CHEATSHEET.md` prompts with your AI coding agent: `scan`, `new feature`,
`status`, `apply`, `review`, and `modify`.

## Tech Stack Naming

Tech stack ids are hierarchical. The default Java reference stack is:

```yaml
tech_stacks:
  - java/ddd-spring
```

Add new stacks under `tech-stacks/tech-contracts/<language>/<style>/`, for example:

```text
tech-stacks/tech-contracts/typescript/nextjs/
tech-stacks/tech-contracts/python/fastapi/
tech-stacks/tech-contracts/go/clean-architecture/
```

Project-owned copies live under `shiki_context/constitution/tech_contracts/` after init.
Users should change those copies instead of editing the read-only framework defaults.

## Repository Shape

```text
user-interface/       user entry surfaces
core-kernel/          runtime rules, task contracts, workflows, templates, helpers
tools-skills/         scripts and reusable skills
tech-stacks/          default tech contracts
providers/            provider adapter boundary
tests/                regression specs and fixtures
```

## Local Verification

```bash
python3 tools-skills/scripts/verify.py
```

The verification script compiles Python helpers, checks references, creates a
sample project, runs init and scan flows with a deterministic `devagent` shim,
and validates package/unpack behavior.
