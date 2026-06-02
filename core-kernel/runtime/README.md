# Runtime

Runtime documents define how Shiki loads context, routes task contracts, and
checks phase gates. Normal execution flows through:

```text
active_task.md -> _plan.md -> task contract -> workflow -> template/tech contract
```

State principles:

- Plain specs express current valid facts.
- Gates check that files exist, are complete, and are consistent.
- L2 AS-IS leaf specs are the default Code/Test fact source.
- `code_contract.md` is only an optional implementation slice.
- Project/module/feature scopes use `README.md` for humans, `index.md` for routing, and `_plan.md` for task/output ledgers.
- Plan items stay atomic even when `/shiki-next` starts an adaptive execution
  session that advances several safe ready items in one invocation.
- Execution sessions choose `single_agent_session` or `agent_team_session`
  automatically from adapter metadata, plan state, context budget, and stop
  conditions; users do not pass a single/team mode.
- Item review is a completion gate. A task is done only after execution,
  verification, review, evidence, and plan state update all pass.
- Multi-step commands such as `sync` and `doctor` create workspace temporary plans before changing files, then execute one item at a time.

Use `phase_contract.md` only as fallback guidance when plan or gate state is
missing. Use `context_loading.md` as the authoritative loading policy and
`execution_session.md` as the `/shiki-next` coordinator policy.
