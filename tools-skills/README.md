# Tools And Skills

This module owns deterministic tools and reusable skills.

- `scripts/`: command-line tools for init, scan, feature creation, adapter installation, verification, and docs publishing.
- `skills/`: reusable agent skills layered on top of tools.

Tools and skills provide capability. Task routing, workflow selection, and evidence acceptance remain Core Kernel responsibilities.

## Publishing Specs

- `spec-to-html`: generic Markdown-to-HTML publishing.
- `pretty-shiki-spec`: Shiki-specific L0 human-friendly HTML generated from
  L1 consensus specs under `shiki_context/`.
