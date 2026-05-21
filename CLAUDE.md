# Shiki Agent Context

Shiki is a workflow-driven AI development harness. Treat this repository as the
read-only framework source; project-specific state belongs in `shiki_context/`
after `tools-skills/scripts/init.py` runs.

## Invariants

- Runtime state is file-backed, not conversation-backed.
- `_plan.md` routes work; task contracts define executable units; workflows are the human-readable execution view.
- `code_contract.md` is the only coding fact source after design is accepted.
- Tech stack rules live under `shiki_context/constitution/tech_contracts/<stack_name>/` in consumer projects.
- Framework defaults under `tech-stacks/tech-contracts/` are copied at init and should remain generic.
- Local maintenance assets such as `CLAUDE.md`, tests, fixtures, and verification scripts stay out of package output.

## Verification

Run this before delivery when core files change:

```bash
python3 tools-skills/scripts/verify.py
```
