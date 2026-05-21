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
Then `shiki_context/workspace/_plan.md` contains init.entrance tasks and init.sync
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
`code_contract.md`, and `tests/test_cases.md` exists
And the bootstrap plan contains the design_init item.

## HIT-006 Design Init Expands Plan

Given a filled Design Brief
When design_init runs
Then `_plan.md` expands to direct design, code_contract, code, and merge tasks
And feature index records generated leaf specs.

## HIT-007 Code Contract Gate

Given model, persistence, ACL, component, entrance, and flow specs
When code_contract generation runs
Then `code_contract.md` contains sections 1-6, unchecked confirmations, and a concrete version.

## HIT-008 Code Tasks Obey Contract

Given a confirmed code contract
When Code tasks run
Then generated code changes only declared targets
And plan output_files are updated.

## HIT-009 Merge Writes Baseline

Given accepted feature overlay specs and verification evidence
When feature_merge runs
Then baseline module specs are updated
And module index paths remain valid.

## HIT-010 Public Surface Is Clean

Given the public Shiki repository
When maintenance verification runs
Then generated packages exclude `shiki_context/`, local fixtures, caches, and verification-only scripts
And no non-English source text, legacy brand references, or company-specific package names remain.
