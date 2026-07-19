# Tools And Skills

This module owns deterministic tools and reusable skills.

- `scripts/`: command-line tools for init, scan, feature creation, adapter installation, verification, and docs publishing.
- `skills/`: reusable agent skills layered on top of tools.

Tools and skills provide capability. Task routing, workflow selection, and evidence acceptance remain Core Kernel responsibilities.

## Publishing Specs

- `spec-to-html`: generic Markdown-to-HTML publishing.
- `pretty-shiki-spec`: Shiki-specific L0 human-friendly HTML generated from
  L1 consensus specs under `shiki_context/`.

## Codebomb Dependencies

Codebomb uses optional external dependencies and keeps them out of the default
Shiki runtime. Prepare them in an isolated project-local venv:

```bash
python3 shiki/tools-skills/scripts/install_codebomb_deps.py download --wheelhouse vendor/codebomb-wheels
python3 shiki/tools-skills/scripts/install_codebomb_deps.py install --wheelhouse vendor/codebomb-wheels
python3 shiki/tools-skills/scripts/install_codebomb_deps.py doctor
```

For an offline environment, run `download` on a compatible machine with network
access, copy `vendor/codebomb-wheels/` into the target project, then run
`install`. `shiki tool codebomb` automatically uses
`.shiki/tools/codebomb/venv/` when it exists.

Start the MCP server without installing the `shiki` command:

```bash
python3 shiki/tools-skills/scripts/codebomb_mcp.py --repo /path/to/java-repo
```

The launcher writes diagnostics to stderr only, then hands stdout to the MCP
stdio protocol.
