# Runtime

## State

- Current-valid leaf specs are the durable facts.
- Task Contracts are minimal signatures; Workflows own execution and project validation.
- `README.md` is human navigation, `index.md` routes specs, and `_plan.md.output_files` is the completion ledger.
- Code/Test use current L2 leaf specs by default; `code_contract.md` is an optional context slice.
- Review is not Task state.

## Orchestrator

The CLI Orchestrator repeatedly performs a single-Task lifecycle:

1. read active scope and Plan;
2. call Task Router and required-input gate;
3. build a minimal Context Envelope;
4. start one fresh Provider session;
5. validate the first status line and output ledger;
6. start a separate Review session at the configured boundary;
7. continue or stop without turning Review prose into edits.

Prompt manual mode skips the outer Orchestrator and Agent Adapter but calls the same Kernel Task Tools from the developer's current session.

## Development Lifecycle

`Init -> Design -> Code -> Test -> Merge`.

Init establishes baseline once. Flow/sequence diagrams are optional review artifacts, not default Plan requirements.

See `context_loading.md`, `execution_session.md`, `phase_contract.md`, task contracts, and Workflows for the stable protocol.
