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
state transitions, topology selection, review gates, and validation. The model
performs bounded plan items against contracts inside an adaptive execution
session. Strong tools can use workers internally; users still invoke the same
commands.

## Core Ideas

- Workflow-driven execution: each task is routed from `_plan.md` to a task contract and a workflow.
- Adaptive execution sessions: `/shiki-next` automatically chooses a
  single-agent or agent-team topology from adapter metadata, task graph, context
  budget, and stop conditions.
- File-backed state: briefs, specs, plans, tech rules, and outputs live in versioned files.
- Current valid specs: the active leaf specs in scope are the source of truth.
- L2 AS-IS specs: code follows current leaf specs directly; `code_contract.md` is only an optional implementation slice.
- Tech contracts: language and architecture rules are replaceable stacks such as `java/ddd-spring`.
- Review gates: task output is not complete until execution, verification,
  review, evidence, and plan state all pass.
- Minimal context: normal tasks load only plan state, direct dependencies, workflow, templates, and selected tech rules.

## Quick Start

Recommended for Code Agent users: ask the coding tool you are already using to
install Shiki into the current project.

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
python3 shiki/tools-skills/scripts/new_feature.py --taskid FEAT-001
```

Then install project-local tool-native adapters and use the canonical Shiki slash
commands directly:

```bash
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool all
```

Use a single tool target when needed:

```bash
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool claude
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool gemini
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool opencode
```

Expected project-local files:

| tool | install target | command files | extra files |
| :--- | :--- | :--- | :--- |
| Codex | `codex` | `.codex/prompts/shiki-*.md` | `.codex/skills/shiki/SKILL.md` |
| Claude Code | `claude` | `.claude/commands/shiki-*.md` | `.claude/agents/shiki-phase-wave.md` |
| Gemini CLI | `gemini` | `.gemini/commands/shiki-*.toml` | - |
| OpenCode | `opencode` | `.opencode/commands/shiki-*.md` | `.opencode/agents/shiki-*.md` |

After install, the primary command surface is:

```text
/shiki-init
/shiki-status
/shiki-next
/shiki-modify <target>
/shiki-review
/shiki-doctor
```

Invoke those commands inside the installed coding tool. If the tool was already
running, reload its command surface or restart the session after installation.

`/shiki-next` is the user-facing coordinator. It starts an adaptive execution
session and does not ask the user to choose single-agent or agent-team mode.
Strong adapters may use bounded batch, phase-wave, or worker delegation
internally when Core Kernel stop rules allow it, but plan state, task contracts,
review gates, `output_files`, evidence, and verification remain controlled by
Shiki Core. `/shiki-sync` remains an advanced compatibility command for explicit
Code -> Spec synchronization; daily sync behavior should be routed through
`modify`, `review`, or `doctor` when possible.

`docs/CHEATSHEET.md` remains the fallback prompt panel for agents without an
installed adapter.

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
docs/                blueprint and prompt cheatsheet
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
deterministic `devagent` shim, validates tool-native adapter files, and checks
docs publishing behavior.
