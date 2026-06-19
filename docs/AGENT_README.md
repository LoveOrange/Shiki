# Shiki Agent README

This guide is for coding agents and AI coding tools that install, update, or
operate Shiki inside a consumer project. It is intentionally procedural. Human
users should start from the repository `README.md`.

## Operating Rules

- Read the consumer project's local instructions before making changes.
- Work from the consumer project root unless the user explicitly asks otherwise.
- Preserve unrelated user changes. Do not overwrite user-owned files.
- Treat `shiki/` as framework source and `shiki_context/` plus
  `shiki.config.yaml` as project-owned state.
- Prefer the `shiki` CLI for public installs. Use the Python scripts inside
  `shiki/` as the deterministic fallback.
- Do not commit, push, or change install style unless the user explicitly asks.

## Install Shiki

If the `shiki` CLI is available, use it:

```bash
shiki install --tool codex
```

Use the adapter that matches the current coding tool:

```bash
shiki install --tool codex
shiki install --tool claude
shiki install --tool gemini
shiki install --tool opencode
```

Use `--tool all` only when the user wants every supported adapter installed:

```bash
shiki install --tool all
```

If the CLI is not installed and network access is available, install it first:

```bash
python3 -m pip install --user git+https://github.com/LoveOrange/Shiki.git
```

If CLI installation is not available, use the low-level project-local path:

```bash
git submodule add https://github.com/LoveOrange/Shiki.git shiki
python3 shiki/tools-skills/scripts/init.py
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
```

## Repair An Existing Install

When a consumer project already has `shiki/`, do not reinstall the framework.
Repair context and adapter files:

```bash
shiki init
shiki adapter install --tool codex
```

Fallback:

```bash
python3 shiki/tools-skills/scripts/init.py
python3 shiki/tools-skills/scripts/install_agent_adapter.py --tool codex
```

The adapter installer updates only Shiki-managed files. If it reports blocked
files, keep them unchanged and report the paths.

## Update Shiki

First identify how `shiki/` is mounted:

```bash
git -C shiki rev-parse --show-toplevel
git submodule status shiki
```

For a submodule install:

```bash
old=$(git -C shiki rev-parse --short HEAD)
git -C shiki fetch origin
git -C shiki checkout main
git -C shiki pull --ff-only origin main
new=$(git -C shiki rev-parse --short HEAD)
git -C shiki log --oneline --no-decorate "$old..$new"
shiki init
shiki adapter install --tool codex
```

Report the old commit, new commit, upstream commits included, files created or
updated, and any blocked user-owned files.

## Create A Feature

```bash
shiki new-feature --taskid FEAT-001
```

Fallback:

```bash
python3 shiki/tools-skills/scripts/new_feature.py --taskid FEAT-001
```

Stop after creating the feature workspace. Do not continue into design work
unless the user asks.

## Command Surface After Install

Use the tool-native command files installed by the adapter:

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

Reload or restart the coding tool after adapter files change. Gemini CLI users
should run `/commands reload`.

## Verification

After install or repair, verify the expected files exist:

```text
shiki/
shiki.config.yaml
shiki_context/
.shiki/adapters/<tool>/manifest.json
```

For framework maintenance inside the Shiki repository, run:

```bash
python3 tools-skills/scripts/verify.py
```

For consumer projects, run the smallest meaningful project verification after
Shiki-driven edits and report the command and result.
