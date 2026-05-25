# pretty-shiki-spec

`pretty-shiki-spec` generates a Shiki-specific, human-friendly L0 HTML spec
from L1 consensus specs under `shiki_context/`.

It is intentionally different from `spec-to-html`:

- `spec-to-html` publishes Markdown as a generic offline documentation site.
- `pretty-shiki-spec` understands Shiki layers, feature plans, module indexes,
  design leaf specs, test specs, and `code_contract.md`.

## Usage

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --title "Shiki Spec" --fail-on-broken-links
```

Publish one feature:

```bash
python shiki/tools-skills/skills/pretty-shiki-spec/scripts/publish_pretty_spec.py shiki_context --feature FEAT-001 --title "FEAT-001 Spec" --fail-on-broken-links
```

The default output is `pretty_shiki_spec/`.

## Contract

The generated L0 site is a review projection. It cites L1 source files and
surfaces missing targets or placeholders, but it is not the source of truth.
Update the L1 specs, then publish again.
