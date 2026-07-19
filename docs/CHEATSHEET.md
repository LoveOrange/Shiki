# Shiki Command Cheatsheet

## Install

```bash
python3 -m pip install --user git+https://github.com/LoveOrange/Shiki.git
shiki install --tool codex
```

Install all Prompt-track adapters with `shiki adapter install --tool all`.
Low-level repair remains available:

```bash
python3 shiki/tools-skills/scripts/init.py
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool all
```

## Collaboration tracks

| Track | Entry | Task session | Review |
| :--- | :--- | :--- | :--- |
| CLI automatic | `shiki next`, `shiki scan`, or `shiki sync` | Fresh Provider process per Task | Separate fresh process at configured boundaries |
| Prompt manual | `/shiki-next` or another adapter command | Current Coding Agent session | Only when the developer invokes `/shiki-review` |

Both tracks use `shiki task next`, `shiki task complete`, the same Plan and Task
Contracts, and the same Context Envelope.

## Prompt commands

```text
/shiki-init
/shiki-scan
/shiki-new-feature <taskid>
/shiki-status
/shiki-next [item]
/shiki-apply [item]
/shiki-modify <target>
/shiki-review [scope]
/shiki-sync
/shiki-doctor
/shiki-fix <finding>
/shiki-web-spec <url-or-target>
```

`/shiki-next` executes exactly one Kernel-prepared Task in the current session,
records completion only on `PASS`, and returns control. `/shiki-apply` is a
compatibility alias with the same one-Task semantics. No Prompt command starts a
batch, phase wave, hidden worker loop, or automatic Review.

## Kernel task tools

```bash
shiki task next [item]
shiki task next --scope sync
shiki task complete <item> --output <path> [--output <path> ...]
shiki task complete <item> --noop "verified no-file result"
shiki plan add-item --parent <item> --id <id> --phase <phase> \
  --target <target> --contract <contract.yaml>
```

The first command returns the authoritative Context Envelope. Completion is
valid only for the active prepared Task and declared outputs.

## Result protocol

Task results start with one of:

```text
PASS
BLOCKED
FAILED
MANUAL_DECISION
```

Review also supports `CHANGE_REQUEST`. Failure statuses never update
`output_files`.

## Generated adapter files

| Tool | Command files | Extra files |
| :--- | :--- | :--- |
| Codex | `.codex/prompts/shiki-*.md` | `.codex/skills/shiki/SKILL.md` |
| Claude Code | `.claude/commands/shiki-*.md` | - |
| Gemini CLI | `.gemini/commands/shiki-*.toml` | - |
| OpenCode | `.opencode/commands/shiki-*.md` | `shiki-runner` and read-only `shiki-reviewer` |

Reload the coding tool after adapter installation when its command surface was
already active.
