# Shiki Blueprint

## North Star

Shiki is a deterministic workflow kernel for controllable AI-assisted software
development. Durable files, not conversation memory, define the current work:

- explicit phases and Plans
- atomic Task Contracts
- deterministic context loading
- replaceable tech contracts
- verifiable outputs and resumable state

## Stable execution atom

One Plan row routed through one Task Contract is the stable execution atom. The
Core Kernel owns routing, the Context Envelope, dependencies, output ownership,
and completion. Providers only perform the prepared Task.

Canonical contracts contain the full goal, inputs, references, output, checks,
retry rule, and `workflow_ref`. Alias contracts contain only `id` and
`canonical`. Task Review is a session concern, not Task Contract or Plan state.

## Dual collaboration tracks

Shiki v4 has two intentional collaboration tracks:

- CLI automatic: Shiki owns orchestration, opens a fresh Provider session for
  every Task, and runs Review in a separate fresh session at configured Task or
  phase boundaries.
- Prompt manual: the developer invokes a tool-native command; the Task runs in
  the current Coding Agent session and Review happens only when requested.

Both tracks use the same Kernel tools, Plan, contracts, workflows, Context
Envelope, and result protocol. They do not share session lifecycle or Review
triggers.

## Design principles

1. Phase machine over chat flow.
2. Files over hidden memory.
3. Task Contracts over prompt templates.
4. Tech contracts as replaceable loadouts.
5. Provider adapters perform Tasks but do not route them.
6. DDD is the reference stack, not a Kernel assumption.
7. `output_files` is the completion ledger; failures do not mutate it.
8. Human control remains visible in the Prompt track.

The public milestone remains a complete loop from Design Brief through current
leaf specs, code, tests, and verified outputs.
