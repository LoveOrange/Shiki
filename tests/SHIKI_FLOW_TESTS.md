# Shiki Flow Regression Spec

This file defines integration scenarios for Shiki maintainers and AI agents. It
is a test specification, not a command log.

## HIT-001 Init Creates Context Store

Given a consumer project contains `shiki/` and `shiki.config.yaml`
When `python shiki/tools-skills/scripts/init.py` runs
Then `shiki_context/workspace`, `project`, `modules`, `features`, and
`constitution/tech_contracts` exist
And selected tech contracts are copied into the project-owned constitution.

## HIT-002 Scan Discovers Entrances

Given a Java DDD Spring sample project
When `scan.py --only s0.1` runs
Then `shiki_context/workspace/_plan.md` contains init.entrance tasks and init.sync routed by `contract`
And project/module indexes are created or updated.

## HIT-003 Dependency Scan Writes Project Specs

Given a devagent-capable environment
When `scan.py --only s0.2` runs
Then project `techstack.md` and `integration.md` are updated from build/config files
And uncertain facts are marked TBD.

## HIT-004 Entry Analysis Produces Module Specs

Given an init.entrance plan row
When the entry analysis workflow runs
Then module `entrances/*.md` and `flows/*.md` are created or updated
And the flow contains a Discovery Log.

## HIT-005 Feature Bootstrap

Given initialized `shiki_context/`
When `new_feature.py --taskid FEAT-001` runs
Then a feature workspace with `design_brief.md`, `_plan.md`, `index.md`,
and `tests/test_cases.md` exists
And the bootstrap plan contains the design_init item.

## HIT-006 Design Init Expands Plan

Given a filled Design Brief
When design_init runs
Then `_plan.md` expands to direct design, code, and merge tasks using Target Outputs
And targets are feature-root relative, not baseline paths
And feature index records generated leaf specs and Baseline Delta guidance.

## HIT-007 L2 Spec Gate

Given model, persistence, ACL, component, entrance, and flow specs
When Code tasks are selected
Then required L2 AS-IS leaf specs exist and are routable from the feature index
And downstream Code/Test items are not marked STALE.

## HIT-008 Code Tasks Obey L2 Specs

Given current L2 AS-IS leaf specs and target source context
When Code tasks run
Then generated code changes only facts declared by those specs
And plan output_files are updated.

## HIT-008A Batch Runner Preserves Task Atoms

Given multiple ready feature plan items and a capable coding agent
When batch or auto runs
Then each selected item still loads its own task contract and workflow
And output_files are updated after each completed item
And the batch stops at Merge, MANUAL_DECISION, BLOCKED, missing input, ambiguous ownership, baseline writes, or failed verification.

## HIT-009 Merge Writes Baseline

Given accepted feature overlay specs and verification evidence
When feature_merge runs
Then baseline module specs are updated
And module index paths remain valid.
And every merge action traces to Baseline Delta.

## HIT-010 Sync Plans Before Applying

Given changed source files or a bounded git diff scope
When sync runs
Then `shiki_context/workspace/sync_plan.md` is created or updated first
And apply_leaf updates at most one target leaf spec from direct source evidence.

## HIT-011 Doctor Is Confirmed And Bounded

Given a context-store maintenance issue
When doctor runs without explicit confirmation
Then it outputs a read-only diagnosis and does not modify files.
When confirmation is provided
Then it creates `shiki_context/workspace/doctor_plan.md`
And apply_item repairs at most one deterministic item.

## HIT-012 Public Surface Is Clean

Given the public Shiki repository
When maintenance verification runs
Then the public source excludes local context, caches, and private transfer scripts
And no non-English source text, legacy brand references, or organization-specific package names remain.

## HIT-013 Adapter Contract Surface

Given Phase 1 tool-native adapters are installed into a consumer project
When adapter regression checks run
Then installed adapter files reference the v1 adapter contract
And the contract defines the Codex, Claude Code, Gemini CLI, and OpenCode capability matrix
And each canonical command maps to Core Kernel entry points before host-tool-specific behavior
And `/shiki-status`, `/shiki-next`, and `/shiki-modify <target>` map to Core Kernel context loading, task contracts, and workflow references
And adapter execution reports `BLOCKED`, `MANUAL_DECISION`, and verification failures without marking incomplete plan items done.

## HIT-014 Adapter Install And Commands

Given a consumer project contains `shiki/`
When `python shiki/tools-skills/scripts/install_agent_adapter.py --tool all` runs
Then Codex, Claude Code, Gemini CLI, and OpenCode project-local command files are created
And repeated installer runs skip matching Shiki-managed files without duplicates
And `/shiki-next` remains the user-facing command while bounded batch, phase-wave, and subagent execution stay internal strategies.

## HIT-015 Claude Code Phase-Wave Adapter

Given the Claude Code adapter is installed into a consumer project
When `/shiki-next` considers phase-wave or subagent delegation
Then `.claude/commands/shiki-next.md` keeps the root session responsible for plan state, dependency checks, `output_files`, and verification
And `.claude/commands/shiki-modify.md` exposes `argument-hint: <target>`
And `.claude/agents/shiki-phase-wave.md` requires a root assignment before edits
And the worker refuses Merge, plan-state updates, missing assignment fields, ambiguous ownership, and failed verification.

## HIT-016 Tool-Native Command Invocation Happy Paths

Given Codex, Claude Code, Gemini CLI, and OpenCode adapters are installed into a consumer project
When a user invokes `/shiki-status`, `/shiki-next`, or `/shiki-modify <target>` from the native command surface
Then each command loads the adapter contract before tool-specific guidance
And `/shiki-status` loads Core Kernel context and remains read-only
And `/shiki-next` loads runner/next, selects an internal execution mode, loads task contracts, and marks `output_files` only after verification
And `/shiki-modify <target>` treats trailing command text as the required bounded target and returns `BLOCKED` when the target is missing or ambiguous
And active tool sessions document the required reload or restart step after command files change.
