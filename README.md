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

Shiki narrows the model's job. The Core Kernel owns task routing, context
loading, dependencies, output-controlled state transitions, and validation. A
provider executes one Kernel-prepared Task at a time.

Shiki sits above provider-local loops. Codex, Claude Code, OpenCode, Gemini, or
future providers can still read, edit, test, and fix inside a bounded
assignment. Shiki owns the project and phase loop: which item is next, which
files are loaded, which gates must pass, what evidence is accepted, and where
the durable state is written.

## Core Ideas

- Workflow-driven execution: each task is routed from `_plan.md` to a task contract and a workflow.
- Provider-backed execution: providers execute bounded assignments; Shiki Core
  owns routing, gates, evidence, and resumable state.
- Dual collaboration tracks: CLI automation uses a fresh Provider session for
  every Task and a separate Review session, while Prompt commands execute one
  Task in the developer's current Coding Agent session with explicit Review.
- File-backed state: briefs, specs, plans, tech rules, and outputs live in versioned files.
- Current valid specs: the active leaf specs in scope are the source of truth.
- L2 AS-IS specs: code follows current leaf specs directly; `code_contract.md` is only an optional implementation slice.
- Project skeleton specs: specs are both model-facing context and a
  human-readable architecture map for technical users.
- Tech contracts: language and architecture rules are replaceable stacks. The
  default reference stack is DDD-oriented, such as `java/ddd-spring`, but DDD is
  not hard-coded into the kernel.
- Output-controlled completion: only a successful Task with validated declared
  outputs updates the Plan ledger; failure statuses leave it unchanged.
- Design reuse gate: design tasks must check reusable baseline/source facts
  before adding new concepts, flows, fields, services, or error codes.
- Test workflow: feature plans can route API cases, unit cases, test code, and
  run-and-route evidence before Merge.
- Minimal context: normal tasks load only plan state, direct dependencies, workflow, templates, and selected tech rules.

See `docs/PHILOSOPHY.md` for the design philosophy behind Shiki's provider
boundary, DDD default stack, task granularity model, and future phase
orchestrators.

## Quick Start

Install the `shiki` CLI first, then install Shiki into the consumer project:

```bash
python3 -m pip install --user git+https://github.com/LoveOrange/Shiki.git
shiki install --tool codex
```

Use `--tool all` to install every supported adapter. `shiki install` mounts the
framework into `shiki/`, initializes `shiki_context/`, and writes the
project-local command files for the selected coding tool.

For Code Agent users, the equivalent natural-language path is to ask the coding
tool you are already using:

```text
Install github.com/LoveOrange/Shiki in this project as shiki/, initialize Shiki,
and install the Shiki adapter for the coding tool I am using now. Preserve any
existing project changes, and tell me which files were created or updated.
```

If the project already contains `shiki/`, use the shorter repair prompt:

```text
Install or repair the Shiki adapter for my current coding tool from the existing
shiki/ directory. Reload the tool command surface if needed.
```

The agent should perform the equivalent local steps below. Use the commands
directly only when you are installing manually or auditing what the agent did.

```bash
git submodule add https://github.com/LoveOrange/Shiki.git shiki
python3 shiki/tools-skills/scripts/init.py
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
```

Initialization creates:

```text
shiki.config.yaml
shiki_context/
  workspace/
  constitution/tech_contracts/
  constitution/team_norm.md
  project/
  modules/
  features/
```

Update Shiki later with the same Code Agent style:

```text
Update the Shiki install in this project to the latest github.com/LoveOrange/Shiki
version. First identify whether shiki/ is a submodule, subtree, or plain checkout.
Record the current Shiki commit, update it using the project's existing install
style, then rerun Shiki init and repair the adapter for my current coding tool.
Preserve unrelated project changes. When finished, report the old commit, new
commit, upstream Shiki commits included in the update, and any project-local
Shiki files or adapter files that were created or updated.
```

For a submodule install, the equivalent manual update is:

```bash
old=$(git -C shiki rev-parse --short HEAD)
git -C shiki fetch origin
git -C shiki checkout main
git -C shiki pull --ff-only origin main
new=$(git -C shiki rev-parse --short HEAD)
git -C shiki log --oneline --no-decorate "$old..$new"
python3 shiki/tools-skills/scripts/init.py
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
```

Create a feature workspace:

```bash
shiki new-feature --taskid FEAT-001
```

Then install project-local tool-native adapters and use the canonical Shiki slash
commands directly:

```bash
shiki adapter install --tool all
```

Use a single tool target when needed:

```bash
shiki adapter install --tool codex
shiki adapter install --tool claude
shiki adapter install --tool gemini
shiki adapter install --tool opencode
```

The Python scripts remain the stable low-level entry points inside `shiki/` for
auditing, offline repair, and deterministic regression checks.

Equivalent low-level adapter commands:

```bash
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool all
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool claude
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool gemini
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool opencode
```

Expected project-local files:

| tool | install target | command files | extra files |
| :--- | :--- | :--- | :--- |
| Codex | `codex` | `.codex/prompts/shiki-*.md` | `.codex/skills/shiki/SKILL.md` |
| Claude Code | `claude` | `.claude/commands/shiki-*.md` | - |
| Gemini CLI | `gemini` | `.gemini/commands/shiki-*.toml` | - |
| OpenCode | `opencode` | `.opencode/commands/shiki-*.md` | `.opencode/agents/shiki-*.md` |

After install, the primary command surface is:

```text
/shiki-init
/shiki-scan
/shiki-new-feature <taskid>
/shiki-status
/shiki-next
/shiki-apply
/shiki-modify <target>
/shiki-review
/shiki-sync
/shiki-doctor
/shiki-fix <stacktrace>
/shiki-web-spec [scope]
```

Invoke those commands inside the installed coding tool. If the tool was already
running, reload its command surface or restart the session after installation.
`/shiki-scan`, `/shiki-new-feature <taskid>`, `/shiki-fix <stacktrace>`, and
`/shiki-web-spec [scope]` provide the utility command surface for setup,
diagnosis, and generated spec views.

`/shiki-next` is the Prompt-track entry. It calls the same deterministic Kernel
tools as the CLI, executes exactly one prepared Task in the developer's current
Coding Agent session, records outputs only on `PASS`, and returns control.
Review runs only when the developer invokes `/shiki-review`. `/shiki-apply` is a
compatibility alias with the same one-Task behavior.

The automatic CLI track is intentionally different: `shiki next`, `shiki scan`,
and `shiki sync` start a fresh configured Provider process for every Task and a
separate fresh process for Review at the configured Task or phase boundary.
Read-only or explicitly scoped CLI Provider commands include `status`, `review`,
`modify`, `fix`, `test`, `doctor`, and `flow`. See `docs/v4-architecture.md` and
`docs/v4-runtime-flows.md`.

`docs/CHEATSHEET.md` remains the fallback prompt panel for agents without an
installed adapter.

`docs/AGENT_README.md` is the procedural guide for coding agents and AI coding
tools that need to install, repair, update, or operate Shiki inside a consumer
project.

Publish a human-friendly L0 review site from Shiki L1 specs:

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --title "Shiki Spec" --fail-on-broken-links
```

## Tech Stack Naming

Tech stack ids are hierarchical. The default Java reference stack is:

```yaml
tech_stacks:
  - java/ddd-spring
```

Add new stacks under `tech-stacks/tech-contracts/<language>/<style>/`, for example:

```text
tech-stacks/tech-contracts/typescript/nextjs/
tech-stacks/tech-contracts/python/default/
tech-stacks/tech-contracts/python/fastapi/
tech-stacks/tech-contracts/go/clean-architecture/
```

Project-owned copies live under `shiki_context/constitution/tech_contracts/` after init.
Users should change those copies instead of editing the read-only framework defaults.

## Repository Shape

```text
docs/                philosophy, blueprint, agent guide, and prompt cheatsheet
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
sample project, runs init, scan, feature, and adapter-install flows with a
deterministic fake Codex executable, and validates tool-native adapter files.
