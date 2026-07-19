# Codebomb POC Design

> Standalone Codebase Asset Engine and read-only MCP server for Java/Python repositories.
> Relationship: `Shiki -> Codebomb`; Codebomb does not depend on Shiki.

- **Status**: Draft for POC implementation
- **Date**: 2026-06-30
- **Primary user**: local Codex / AI coding agents / Shiki runtime
- **Short name**: `codebomb`
- **Meaning**: “code big bang” — explode a codebase into queryable architecture/code assets
- **POC language scope**: Java + Python
- **POC backend decision**: native Codebomb implementation using Tree-sitter + LSP
- **Explicit non-decision**: Serena is not a runtime dependency, not wrapped, and not used as a fallback

---

## 0. Codex Implementation Prompt

Use this prompt in a **fresh Codebomb repository** or in an isolated `external-tools/codebomb/` incubation directory. Prefer a new repository if possible.

```text
We are building a standalone tool named codebomb.

Technology decision:
- Codebomb is independent from Shiki.
- Shiki may consume Codebomb through MCP.
- Shiki may add a thin external-tool launcher named `shiki tool codebomb`.
- Do not implement the Codebomb engine, indexer, MCP server, Tree-sitter extraction, or LSP integration inside Shiki.
- Do not import Shiki code.
- If a Shiki launcher is implemented later, it must exec the `codebomb` CLI instead of importing Codebomb internals.
- Do not integrate Serena.
- Do not call or wrap Serena.
- Do not implement backend fallback logic.

POC product goal:
A user can run one command to start a read-only MCP server for a local Java/Python repository:

  codebomb serve --repo . --profile semantic --transport stdio

Shiki users should be able to start the same external server through:

  shiki tool codebomb serve --repo . --profile semantic --transport stdio

The Shiki command is only a launcher. The server remains Codebomb-owned.

The server exposes query tools over Codebomb-owned codebase assets generated from Tree-sitter and LSP facts.

Implementation strategy:
Do one small reviewable PR at a time. Start with the smallest skeleton PR.

PR 1 scope:
1. Create independent Python package `codebomb`.
2. Add CLI command `codebomb`.
3. Add command: `codebomb status --repo .`.
4. Add command: `codebomb serve --repo . --profile syntax --transport stdio`.
5. Add a read-only MCP server with only `codebomb.status` and `codebomb.index_status` tools.
6. Add repository root resolution and workspace jail checks.
7. Add tests for CLI status and MCP tool registration if practical.
8. No Tree-sitter yet.
9. No LSP yet.
10. No Shiki changes.

Separate Shiki integration PR scope:
1. Add `shiki tool codebomb` as an external command dispatcher.
2. Locate an installed `codebomb` executable on PATH or from explicit `--command`.
3. Forward `status`, `index`, and `serve` arguments to Codebomb without importing it.
4. For `serve --transport stdio`, do not write anything to stdout before handing control to Codebomb.
5. Add tests with a fake `codebomb` executable to verify argument forwarding and stdout cleanliness.

Before editing:
- Show exact files to create or edit.
- Show dependencies.
- Show test commands.
- Ask for approval.
```

---

## 1. Executive Summary

Codebomb is a standalone code intelligence tool that turns a local source repository into queryable codebase assets and exposes them through a read-only MCP server.

The first useful POC target is:

```bash
codebomb serve --repo . --profile semantic --transport stdio
```

It should:

1. Resolve and validate a local repository root.
2. Build or read Codebomb-owned codebase assets.
3. Extract Java and Python structural facts with Tree-sitter.
4. Enrich selected facts with Java/Python LSP servers.
5. Start a read-only MCP server over stdio.
6. Let Codex or Shiki query code context without manually scanning the whole repository.

Codebomb is **not** a Shiki module. Shiki treats Codebomb as an external code context provider:

```text
Shiki workflow/task contract
  -> MCP client/tool call
    -> codebomb MCP server
      -> L2 Codebase Assets
      -> L1 Model Context Pack
```

This separation keeps Shiki lightweight and allows Codebomb to evolve as an independent code intelligence product.

For Shiki users, the intended launch command is:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
```

This command must be a thin wrapper around `codebomb serve`, not a second implementation.

---

## 2. Relationship Between Shiki And Codebomb

### 2.1 Dependency Direction

```text
shiki -> codebomb
```

Shiki may launch Codebomb or call Codebomb through MCP, but Codebomb must not import, depend on, or assume Shiki.

### 2.2 Integration Principle

Shiki should not know how Java LSP, Python LSP, Tree-sitter grammar loading, index caching, or symbol extraction works. Shiki should only know that a Codebomb MCP server exposes tools such as:

```text
codebomb.status
codebomb.index_status
codebomb.search_symbol
codebomb.get_symbol
codebomb.get_symbol_source
codebomb.find_references
codebomb.build_context_pack
```

### 2.3 Current Shiki Surface

The current Shiki implementation is a small Python CLI package:

```text
pyproject.toml -> shiki = "shiki_cli.cli:main"
shiki_cli/cli.py -> argparse command dispatcher
```

Current public CLI commands are:

```text
shiki install
shiki init
shiki new-feature
shiki adapter install
```

The CLI either installs the framework or dispatches to project-local scripts under `shiki/tools-skills/scripts/`. The adapter installer writes tool-native command files and manifests under the consumer project, for example:

```text
.codex/prompts/shiki-*.md
.codex/skills/shiki/SKILL.md
.claude/commands/shiki-*.md
.gemini/commands/shiki-*.toml
.opencode/commands/shiki-*.md
.shiki/adapters/<tool>/manifest.json
```

There is no current `shiki tool` namespace and no current MCP process launcher.

### 2.4 Target Shiki Tool Namespace

Add a `tool` namespace for external tools that are useful to Shiki workflows but are not part of Shiki Core:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
shiki tool codebomb status --repo .
shiki tool codebomb index --repo . --profile syntax
```

The launcher behavior should be deliberately small:

1. Resolve the consumer project root from `--project-root` or the current directory.
2. Resolve `--repo` relative to the project root unless it is absolute.
3. Find the `codebomb` executable from PATH, or from an explicit launcher option such as `--command /path/to/codebomb`.
4. Forward only Codebomb CLI arguments to the external process.
5. Never import Codebomb Python modules.
6. Never write Shiki state or `shiki_context/` files.
7. For MCP stdio mode, reserve stdout for the MCP protocol and send launcher diagnostics only to stderr.

The existing `run()` helper in `shiki_cli/cli.py` prints `$ ...` to stdout, so it must not be reused for MCP stdio serving. The stdio path should use `os.execvp` or an equivalent no-stdout handoff.

### 2.5 Shiki Runtime Behavior Through MCP

When Codebomb MCP is configured and available, Shiki Code/Design/Test tasks may call `codebomb.build_context_pack` before manually loading source files.

When Codebomb MCP is unavailable, Shiki should report that the code context provider is missing. It should not silently emulate Codebomb with broad repository scans.

---

## 3. Product Thesis

Most AI coding agents waste time and tokens because they explore repositories through repeated directory listings, grep calls, and full-file reads.

Codebomb reduces that waste by precomputing and serving code facts:

```text
file inventory
symbol inventory
method/function/class signatures
source ranges
imports
references
definitions
call-ish relationships
context packs
```

The goal is not to replace source loading. The goal is to make source loading precise.

```text
Bad:
  Agent reads large directories and many full files to discover context.

Better:
  Agent asks Codebomb for the task-relevant symbols, ranges, definitions, references, and suggested source slices.
```

---

## 4. Technical Decision Record

### ADR-001: Codebomb Is Standalone

**Status**: Accepted for POC.

**Decision**: Build Codebomb as an independent tool. Shiki consumes it through MCP.

**Rationale**:

- Codebomb has heavy dependencies and lifecycle concerns: Tree-sitter grammars, LSP servers, language-specific indexing, cache formats, MCP serving.
- Shiki should stay focused on workflow, specs, task contracts, gates, and AI delivery orchestration.
- Codebomb can be useful outside Shiki, including direct Codex/Claude/Gemini/OpenCode use.

**Consequences**:

- Codebomb has its own package, CLI, tests, and release cadence.
- Shiki integration is through MCP configuration and workflow guidance, not imports.
- Codebomb can later become a separate public project.

---

### ADR-002: Native Backend, No Serena Runtime Dependency

**Status**: Accepted for POC.

**Decision**: Implement Codebomb’s own MCP server, asset schema, index store, Tree-sitter extraction, and LSP integration. Serena is not used as a backend, wrapper, or fallback.

**Rationale**:

Serena is a strong MCP coding toolkit, but Codebomb’s goal is not merely to expose IDE-like semantic tools. Codebomb needs its own L2/L1/L0 asset standard, freshness metadata, context-pack semantics, and Shiki-facing contract.

Using Serena as the first backend would mostly validate “Serena is useful,” not “Codebomb’s asset model is correct.”

**Consequences**:

- POC has more implementation work.
- POC has fewer language capabilities than Serena initially.
- Codebomb owns its MCP tool names, schemas, storage layout, and context-pack output.
- Future Serena comparison or migration requires a new ADR. It must not be added as silent fallback behavior.

---

### ADR-003: Profiles Are Explicit Modes, Not Fallbacks

**Status**: Accepted for POC.

**Decision**: Codebomb supports explicit profiles:

```text
syntax   = Tree-sitter structural assets only
semantic = Tree-sitter + LSP semantic assets
```

If `semantic` is requested and required LSP dependencies are missing, Codebomb fails with actionable setup instructions. It does **not** silently downgrade to `syntax`.

**Rationale**:

Fallback behavior hides tool quality and makes AI context unreliable. Explicit profiles make the asset quality and dependencies visible.

**Consequences**:

- Users choose speed/minimal dependencies with `syntax`.
- Users choose richer semantics with `semantic`.
- MCP results include profile and freshness metadata.

---

## 5. Goals And Non-Goals

### 5.1 POC Goals

- Provide an independent `codebomb` CLI.
- Start a read-only MCP server with one command.
- Support local repository paths first.
- Support Java and Python.
- Build Codebomb-owned L2 asset files.
- Support Tree-sitter structural scanning for Java and Python.
- Support LSP semantic enrichment for Java and Python in `semantic` profile.
- Expose MCP tools for status, file inventory, symbol search, symbol source, references, and context-pack generation.
- Keep all MCP tools read-only.
- Attach freshness, profile, extractor, confidence, and source-range metadata to query results.

### 5.2 POC Non-Goals

- No Shiki internal implementation.
- No Serena integration.
- No fallback backend selection.
- No remote repo clone in the first POC.
- No editing/refactoring/write MCP tools.
- No shell execution MCP tools.
- No full architecture diagram generation in the first POC.
- No complete call graph guarantee.
- No production security sandbox beyond local workspace jail and read-only behavior.
- No support for every language.

---

## 6. External Technical Basis

This section summarizes why the selected technologies are suitable.

### 6.1 MCP

The official MCP Python SDK supports building MCP servers that expose tools, resources, and prompts, and it supports standard transports such as stdio, Streamable HTTP, and SSE. The current README warns that SDK v2 is pre-release and recommends v1.x for production, so the POC should pin the stable v1 line with `<2` upper bound.

Reference: https://github.com/modelcontextprotocol/python-sdk

### 6.2 MCP Security

MCP’s own security guidance calls out risks around local MCP server compromise, stdio transport security, scope minimization, and other attack vectors. Codebomb’s first server must therefore be read-only, stdio-first, workspace-jailed, and must not expose shell or write tools.

Reference: https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices

### 6.3 Tree-sitter

Tree-sitter is a parser generator and incremental parsing library. It builds concrete syntax trees, updates them efficiently as files are edited, is designed to be fast enough for editor keystroke parsing, and has upstream parsers for Java and Python.

Reference: https://tree-sitter.github.io/tree-sitter/

### 6.4 Java LSP

Eclipse JDT LS supports Java projects, Maven, Gradle, standalone Java files, syntax/compilation diagnostics, code navigation, references/implementations, call hierarchy, and type hierarchy. It requires Java 21 runtime to run.

Reference: https://github.com/eclipse-jdtls/eclipse.jdt.ls

### 6.5 Python LSP

`python-lsp-server` exposes a Python language server with features including go to definition, hover, find references, document symbols, signature help, linting, and formatting capabilities.

Reference: https://github.com/python-lsp/python-lsp-server

---

## 7. Conceptual Asset Layers

Codebomb owns three conceptual layers.

```text
L2 Codebase Assets    machine facts extracted from code
L1 Model Context Pack task/query-scoped model context derived from L2
L0 Human Views        diagrams/reports derived from L2/L1 for humans
```

### 7.1 L2 Codebase Assets

L2 is the source of machine-readable code facts.

Examples:

```text
files
symbols
source ranges
signatures
imports
definitions
references
outlines
language/server diagnostics
extractor metadata
hash/freshness metadata
```

L2 should be deterministic and reproducible. It should not contain free-form AI summaries as facts.

### 7.2 L1 Model Context Pack

L1 is generated for an AI task or query.

Examples:

```text
source slices
symbol metadata
direct definitions
references
related tests
entrypoint hints
freshness
excluded files and reasons
estimated token cost
```

L1 is what Codex/Shiki loads into the working context.

### 7.3 L0 Human Views

L0 is for humans.

Examples:

```text
component diagrams
sequence diagrams
class diagrams
dependency maps
impact review reports
architecture drift reports
```

L0 is deferred until after the core POC. Do not implement L0 diagrams in the first POC.

---

## 8. CLI Design

### 8.1 Codebomb Native Commands

```bash
codebomb status --repo .
codebomb index --repo . --profile syntax
codebomb index --repo . --profile semantic
codebomb serve --repo . --profile semantic --transport stdio
codebomb query search-symbol --repo . "OrderService"
codebomb query get-symbol --repo . "<symbol_id>"
codebomb query source --repo . "<symbol_id>"
codebomb pack --repo . --query "OrderService.createOrder" --budget 12000
```

### 8.2 Shiki-Mediated Commands

Shiki should expose Codebomb through an external-tool namespace, not through a new slash command and not through Shiki Core task contracts:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
shiki tool codebomb status --repo .
shiki tool codebomb index --repo . --profile syntax
```

For user ergonomics, the POC may allow this shortcut:

```bash
shiki tool codebomb --repo . --profile semantic --transport stdio
```

Shortcut rule:

```text
If the token after `codebomb` is missing or starts with `-`, treat the command as `serve`.
```

The canonical form remains explicit:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
```

### 8.3 Shiki Launcher Contract

`shiki tool codebomb` is a process launcher with these constraints:

```text
Input:
  shiki tool codebomb [serve|status|index] [codebomb args...]

Output:
  external Codebomb process output

Allowed Shiki-side behavior:
  resolve project root
  resolve repo path
  locate codebomb executable
  pass arguments through
  return the Codebomb exit code

Forbidden Shiki-side behavior:
  import codebomb modules
  parse .codebomb/cache asset files
  implement MCP tools
  implement indexing
  write shiki_context/
  print command banners to stdout in stdio serving mode
```

Suggested first implementation in the existing Shiki CLI:

```text
shiki_cli/cli.py
  add `tool` subparser
  add `codebomb` nested command
  parse remaining args with argparse.REMAINDER or equivalent
  normalize default command to `serve`
  use shutil.which("codebomb") unless --command is supplied
  for `serve --transport stdio`, exec the process without stdout prelude
```

The existing `shiki` CLI uses `argparse` and already has `ensure_project_root()`. Reuse project-root validation, but do not reuse the helper that prints commands before running them.

Later Shiki may pass through `query` or `pack`, but the POC should keep the Shiki surface focused on starting and checking the external MCP server. Query usage should happen through MCP tools.

### 8.4 POC Server Command

```bash
codebomb serve --repo . --profile semantic --transport stdio
```

Shiki-mediated equivalent:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
```

Behavior:

1. Resolve `--repo` to an absolute path.
2. Enforce workspace jail.
3. Load `.codebomb/cache/manifest.json` if present.
4. If index is missing, either:
   - fail with `INDEX_MISSING`, or
   - optionally support `--index-if-missing` in later PR.
5. Start MCP server over stdio.
6. Expose read-only tools.

For the smallest first server PR, use:

```bash
codebomb serve --repo . --profile syntax --transport stdio
shiki tool codebomb serve --repo . --profile syntax --transport stdio
```

and expose only status tools.

### 8.5 Local-Only POC

The POC should support local paths only:

```bash
codebomb serve --repo .
shiki tool codebomb serve --repo .
```

Do not support:

```bash
codebomb serve --repo https://github.com/org/repo
shiki tool codebomb serve --repo https://github.com/org/repo
```

Remote clone support can be added later with explicit security and cache rules.

---

## 9. MCP Server Design

### 9.1 Transport

POC transport:

```text
stdio only
```

HTTP transport is deferred.

### 9.2 Server Instructions

The MCP server should return concise server-wide instructions similar to:

```text
Codebomb provides read-only code intelligence for the configured repository.
Use build_context_pack before reading many source files.
Prefer symbol, reference, definition, and source-range tools over full-repository scans.
All results include profile, freshness, extractor, and source-range metadata when available.
This server does not write files, run shell commands, or edit code.
```

### 9.3 MCP Tools

#### `codebomb.status`

Returns basic server and repo state.

```json
{
  "name": "codebomb",
  "version": "0.1.0",
  "repo_root": "/abs/path/repo",
  "profile": "semantic",
  "read_only": true,
  "indexed": true,
  "languages": ["java", "python"]
}
```

#### `codebomb.index_status`

Returns index freshness.

```json
{
  "repo_root": "/abs/path/repo",
  "profile": "semantic",
  "freshness": "current",
  "git_commit": "abc123",
  "dirty": false,
  "indexed_at": "2026-06-30T12:00:00Z",
  "files": 128,
  "symbols": 934,
  "references": 412
}
```

#### `codebomb.list_files`

Inputs:

```json
{
  "language": "java",
  "limit": 100
}
```

Outputs file assets.

#### `codebomb.search_symbol`

Inputs:

```json
{
  "query": "OrderService",
  "kind": "class",
  "language": "java",
  "limit": 20
}
```

Outputs matching symbols without source bodies by default.

#### `codebomb.get_symbol`

Inputs:

```json
{
  "symbol_id": "java:src/main/java/com/acme/order/OrderService.java:OrderService.createOrder"
}
```

Outputs symbol metadata.

#### `codebomb.get_symbol_source`

Inputs:

```json
{
  "symbol_id": "...",
  "max_lines": 160
}
```

Outputs source slice if within workspace jail and line budget.

#### `codebomb.find_references`

Inputs:

```json
{
  "symbol_id": "...",
  "limit": 50
}
```

Outputs reference assets. In `syntax` profile, this may return an explicit `UNAVAILABLE_IN_PROFILE` error.

#### `codebomb.find_definition`

Inputs:

```json
{
  "file": "src/main/java/com/acme/order/OrderController.java",
  "line": 42,
  "character": 18
}
```

Outputs definition location from LSP. Only available in `semantic` profile.

#### `codebomb.get_file_outline`

Inputs:

```json
{
  "file": "src/main/java/com/acme/order/OrderService.java"
}
```

Outputs nested symbols for a file.

#### `codebomb.build_context_pack`

Inputs:

```json
{
  "query": "OrderService.createOrder",
  "budget_tokens": 12000,
  "purpose": "code_implementation"
}
```

Outputs L1 context pack.

---

## 10. Asset Store Layout

Codebomb should store local generated assets under the repository root:

```text
.codebomb/
  config.yaml                  # optional, later
  cache/
    manifest.json
    files.jsonl
    symbols.jsonl
    references.jsonl
    definitions.jsonl
    outlines.jsonl
    diagnostics.jsonl
    context_packs/
      <pack_id>.json
    lsp/
      java/
      python/
```

### 10.1 Git Policy

Default recommendation:

```text
.codebomb/cache/ should not be committed.
```

If teams later want commit-friendly generated views, use a separate export command:

```bash
codebomb export --repo . --format markdown --output codebomb_views/
```

That is outside the first POC.

### 10.2 JSONL First, SQLite Later

POC should use JSONL for simplicity.

SQLite can be introduced after schemas stabilize.

---

## 11. L2 Asset Schema

### 11.1 Manifest

```json
{
  "schema_version": "codebomb.l2.v0",
  "repo_root": "/abs/path/repo",
  "profile": "semantic",
  "languages": ["java", "python"],
  "git_commit": "abc123",
  "dirty": false,
  "indexed_at": "2026-06-30T12:00:00Z",
  "extractors": {
    "tree_sitter": {
      "enabled": true,
      "languages": ["java", "python"]
    },
    "lsp": {
      "enabled": true,
      "servers": {
        "java": "jdtls",
        "python": "pylsp"
      }
    }
  },
  "counts": {
    "files": 128,
    "symbols": 934,
    "references": 412
  }
}
```

### 11.2 FileAsset

```json
{
  "id": "file:src/main/java/com/acme/order/OrderService.java",
  "path": "src/main/java/com/acme/order/OrderService.java",
  "language": "java",
  "sha256": "...",
  "size_bytes": 12345,
  "line_count": 280,
  "indexed_at": "2026-06-30T12:00:00Z",
  "git_commit": "abc123",
  "dirty": false
}
```

### 11.3 SymbolAsset

```json
{
  "id": "java:src/main/java/com/acme/order/OrderService.java:OrderService.createOrder(CreateOrderCommand)",
  "kind": "method",
  "language": "java",
  "name": "createOrder",
  "qualified_name": "com.acme.order.OrderService.createOrder",
  "signature": "Order createOrder(CreateOrderCommand command)",
  "file": "src/main/java/com/acme/order/OrderService.java",
  "range": {
    "start_line": 42,
    "start_character": 2,
    "end_line": 96,
    "end_character": 3
  },
  "selection_range": {
    "start_line": 42,
    "start_character": 8,
    "end_line": 42,
    "end_character": 19
  },
  "parent_symbol_id": "java:src/main/java/com/acme/order/OrderService.java:OrderService",
  "visibility": "public",
  "extractors": ["tree-sitter", "lsp"],
  "confidence": 0.95,
  "sha256": "..."
}
```

### 11.4 ReferenceAsset

```json
{
  "id": "ref:java:...",
  "from_file": "src/main/java/com/acme/order/OrderController.java",
  "from_range": {
    "start_line": 28,
    "start_character": 14,
    "end_line": 28,
    "end_character": 25
  },
  "to_symbol_id": "java:src/main/java/com/acme/order/OrderService.java:OrderService.createOrder(CreateOrderCommand)",
  "kind": "reference",
  "source": "lsp",
  "confidence": 0.9
}
```

### 11.5 DiagnosticAsset

```json
{
  "file": "src/main/java/com/acme/order/OrderService.java",
  "range": {
    "start_line": 42,
    "start_character": 2,
    "end_line": 42,
    "end_character": 18
  },
  "severity": "warning",
  "source": "jdtls",
  "message": "..."
}
```

---

## 12. Java And Python Extraction Scope

### 12.1 Python Tree-sitter Scope

Extract:

```text
module file
class_definition
function_definition
method definitions inside class
imports
from-imports
async functions
```

Symbol kinds:

```text
module
class
function
method
import
```

Signature format examples:

```text
def create_feature(context_dir, shiki_root, task_id)
async def handle(request)
class FeaturePlan
```

### 12.2 Java Tree-sitter Scope

Extract:

```text
package declaration
imports
class declarations
interface declarations
enum declarations
record declarations, if grammar exposes them
constructors
methods
fields
annotations on classes/methods when practical
```

Symbol kinds:

```text
package
class
interface
enum
record
constructor
method
field
import
```

Signature format examples:

```text
public Order createOrder(CreateOrderCommand command)
private void validate(Order order)
public class OrderService
```

### 12.3 LSP Semantic Scope

For `semantic` profile, enrich with:

```text
document symbols
definitions
references
diagnostics
```

Defer:

```text
rename
code actions
formatting
call hierarchy
type hierarchy
workspace edits
```

Call hierarchy can be added after basic references are stable.

---

## 13. LSP Server Selection

### 13.1 Java

Use Eclipse JDT LS.

Expected binary/command options:

```text
jdtls
```

or explicit config:

```yaml
lsp:
  java:
    command: ["jdtls"]
```

Semantic profile should fail clearly if JDT LS is not available.

Example failure:

```json
{
  "error": "LSP_SERVER_MISSING",
  "language": "java",
  "server": "jdtls",
  "message": "semantic profile requires Eclipse JDT LS for Java. Install jdtls and ensure Java 21 runtime is available."
}
```

### 13.2 Python

Use `python-lsp-server` / `pylsp` for the first POC.

Expected command:

```text
pylsp
```

or explicit config:

```yaml
lsp:
  python:
    command: ["pylsp"]
```

Failure:

```json
{
  "error": "LSP_SERVER_MISSING",
  "language": "python",
  "server": "pylsp",
  "message": "semantic profile requires python-lsp-server. Install python-lsp-server and ensure pylsp is on PATH."
}
```

---

## 14. Context Pack Design

### 14.1 Purpose

`codebomb.build_context_pack` produces model-loadable context from L2 assets. It should reduce full-repo reading.

### 14.2 Inputs

```json
{
  "query": "OrderService.createOrder",
  "symbol_id": null,
  "file": null,
  "budget_tokens": 12000,
  "purpose": "code_implementation",
  "include_source": true
}
```

### 14.3 Output

```json
{
  "schema_version": "codebomb.l1.context_pack.v0",
  "pack_id": "ctx_...",
  "repo_root": "/abs/path/repo",
  "profile": "semantic",
  "freshness": {
    "git_commit": "abc123",
    "dirty": false,
    "indexed_at": "2026-06-30T12:00:00Z"
  },
  "query": "OrderService.createOrder",
  "budget_tokens": 12000,
  "estimated_tokens": 6420,
  "primary_symbols": [
    {
      "symbol_id": "...",
      "reason": "best match for query"
    }
  ],
  "source_slices": [
    {
      "file": "src/main/java/com/acme/order/OrderService.java",
      "range": {
        "start_line": 42,
        "end_line": 96
      },
      "symbol_id": "...",
      "reason": "primary implementation target",
      "text": "..."
    }
  ],
  "references": [
    {
      "from_file": "...",
      "from_range": {"start_line": 28, "end_line": 28},
      "reason": "direct LSP reference"
    }
  ],
  "excluded": [
    {
      "path": "target/",
      "reason": "excluded build output"
    }
  ]
}
```

### 14.4 Ranking Rules

Initial ranking:

1. Exact symbol name match.
2. Qualified name match.
3. Filename match.
4. LSP references to primary symbol.
5. Same file sibling symbols.
6. Tests matching symbol/file name.
7. Avoid generated/build/vendor directories.

### 14.5 Budget Rule

Use a conservative token estimate:

```text
estimated_tokens = ceil(char_count / 4)
```

Do not exceed budget. If the primary symbol source exceeds budget, return metadata and a `SOURCE_TOO_LARGE` warning with range information.

---

## 15. Security Model

### 15.1 First POC Security Defaults

```text
read-only MCP tools only
stdio transport only
workspace jail under repo root
no shell execution
no build/test execution
no file writes from MCP tools
no remote clone
no reading outside repo root
no indexing .git internals
no indexing common dependency/build directories
```

### 15.2 Default Exclusions

```text
.git/
.codebomb/cache/
node_modules/
target/
build/
dist/
out/
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.gradle/
.idea/
.vscode/
*.class
*.jar
*.war
*.pyc
```

### 15.3 Secret-Aware Exclusions

Default skip names:

```text
.env
.env.*
*.pem
*.key
id_rsa
id_ed25519
secrets.*
credentials.*
```

### 15.4 MCP Tool Restrictions

Do not expose:

```text
run_shell
edit_file
write_file
rename_symbol
apply_patch
run_tests
install_dependency
```

These may be considered in future only with a separate ADR and explicit preview/approval model.

---

## 16. Package Structure

Recommended independent repository:

```text
codebomb/
  README.md
  pyproject.toml
  src/
    codebomb/
      __init__.py
      cli.py
      config.py
      paths.py
      hashing.py
      store.py
      models.py
      mcp_server.py
      context_pack.py
      scanners/
        __init__.py
        inventory.py
        treesitter_java.py
        treesitter_python.py
      lsp/
        __init__.py
        client.py
        jdtls.py
        pylsp.py
      profiles.py
  tests/
    fixtures/
      python-sample/
      java-sample/
    test_cli_status.py
    test_store.py
    test_inventory.py
    test_treesitter_python.py
    test_treesitter_java.py
    test_context_pack.py
  docs/
    DESIGN.md
    ADRS.md
```

If incubated inside Shiki temporarily:

```text
external-tools/codebomb/
```

The code must still not import Shiki modules.

---

## 17. Implementation Plan

### PR 1: Independent CLI + MCP Skeleton

Goal:

```bash
codebomb status --repo .
codebomb serve --repo . --profile syntax --transport stdio
```

MCP tools:

```text
codebomb.status
codebomb.index_status
```

Scope:

- `pyproject.toml`
- package skeleton
- CLI parser
- repo root resolution
- workspace jail helper
- MCP server skeleton
- tests for status behavior

No indexing yet.

---

### PR 2: File Inventory And Asset Store

Goal:

```bash
codebomb index --repo . --profile syntax
```

Outputs:

```text
.codebomb/cache/manifest.json
.codebomb/cache/files.jsonl
```

Scope:

- file inventory scanner
- exclusion policy
- SHA-256 hashing
- manifest writing
- `codebomb.list_files` MCP tool

---

### PR 3: Tree-sitter Java + Python Symbol Index

Goal:

```bash
codebomb index --repo . --profile syntax
codebomb query search-symbol --repo . "create_feature"
```

Outputs:

```text
.codebomb/cache/symbols.jsonl
```

MCP tools:

```text
codebomb.search_symbol
codebomb.get_symbol
codebomb.get_symbol_source
codebomb.get_file_outline
```

Scope:

- Tree-sitter grammar loading for Java and Python
- symbol extraction
- signature extraction
- line/character ranges
- source slice retrieval

---

### PR 4: LSP Semantic Profile

Goal:

```bash
codebomb index --repo . --profile semantic
```

MCP tools:

```text
codebomb.find_definition
codebomb.find_references
```

Scope:

- LSP client abstraction
- `pylsp` integration
- `jdtls` integration
- document symbols, definitions, references
- clear failure when semantic dependencies are missing

---

### PR 5: Context Pack v0

Goal:

```bash
codebomb pack --repo . --query "OrderService.createOrder" --budget 12000
```

MCP tool:

```text
codebomb.build_context_pack
```

Scope:

- context pack schema
- query resolution
- source slice selection
- reference inclusion
- token budget estimate
- pack persistence under `.codebomb/cache/context_packs/`

---

### PR 6: Shiki External Tool Launcher

Goal:

Start Codebomb MCP through Shiki without making Codebomb a Shiki dependency.

Commands:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
shiki tool codebomb status --repo .
shiki tool codebomb index --repo . --profile syntax
```

Scope:

- Add `tool` namespace to `shiki_cli/cli.py`.
- Add `codebomb` external-tool dispatcher.
- Support `--project-root` using the same consumer-project convention as other Shiki commands.
- Support optional `--command` to point at a Codebomb executable.
- Resolve relative `--repo` against the project root.
- Return Codebomb's exit code.
- For `serve --transport stdio`, avoid all stdout prelude and hand off cleanly.
- Do not add Codebomb package dependencies to `pyproject.toml`.
- Do not import Codebomb internals.
- Do not edit adapter command files in this PR unless a later workflow explicitly needs Codebomb-aware prompts.

Tests:

```text
fake codebomb executable on PATH records argv
`shiki tool codebomb status --repo .` forwards status args
`shiki tool codebomb --repo . --profile syntax --transport stdio` defaults to serve
stdio serve path emits no Shiki banner on stdout
```

Documentation:

- Add sample Codex MCP config using `command = "shiki"` and `args = ["tool", "codebomb", "serve", ...]`.
- Document direct `command = "codebomb"` as the fallback for users who do not want the Shiki launcher.
- Tell Shiki task guidance to call `codebomb.build_context_pack` before broad source scanning when the MCP server is configured.

---

## 18. Testing Plan

### 18.1 Unit Tests

- repo root resolution
- workspace jail
- exclusion rules
- file hashing
- JSONL read/write
- search ranking
- context pack budgeting

### 18.2 Fixture Tests

Python fixture:

```text
python-sample/
  app/service.py
  app/model.py
  tests/test_service.py
```

Java fixture:

```text
java-sample/
  src/main/java/com/acme/order/OrderService.java
  src/main/java/com/acme/order/OrderController.java
  src/test/java/com/acme/order/OrderServiceTest.java
```

### 18.3 LSP Integration Tests

LSP tests should be marked integration and skipped unless the server is installed:

```python
pytest.mark.integration
pytest.importorskip(...)
```

or environment-controlled:

```bash
CODEBOMB_RUN_LSP_TESTS=1 pytest
```

### 18.4 MCP Tests

Use either:

- direct server object test if SDK supports it cleanly, or
- subprocess stdio smoke test.

POC MCP smoke:

```text
start codebomb serve over stdio
call codebomb.status
assert read_only true
assert repo_root correct
```

### 18.5 Shiki Launcher Tests

After the Shiki-side PR exists, add CLI tests with a fake `codebomb` executable:

```text
PATH=<tmp>/bin:$PATH shiki tool codebomb status --repo .
assert fake executable saw: status --repo <resolved-repo>
assert process exit code is propagated
```

For MCP stdio serving:

```text
PATH=<tmp>/bin:$PATH shiki tool codebomb serve --repo . --profile syntax --transport stdio
assert stdout contains only fake Codebomb output
assert stdout does not contain "$ codebomb" or Shiki banners
```

Run Shiki framework verification after changing the launcher:

```bash
python3 tools-skills/scripts/verify.py
```

---

## 19. Error Handling

Use structured errors.

### INDEX_MISSING

```json
{
  "error": "INDEX_MISSING",
  "message": "No Codebomb index found. Run `codebomb index --repo . --profile semantic` first."
}
```

### PROFILE_UNAVAILABLE

```json
{
  "error": "PROFILE_UNAVAILABLE",
  "profile": "semantic",
  "message": "semantic profile requires LSP server dependencies."
}
```

### LSP_SERVER_MISSING

```json
{
  "error": "LSP_SERVER_MISSING",
  "language": "java",
  "server": "jdtls",
  "message": "Install Eclipse JDT LS and ensure Java 21 runtime is available."
}
```

### OUTSIDE_WORKSPACE

```json
{
  "error": "OUTSIDE_WORKSPACE",
  "message": "Requested path is outside the configured repository root."
}
```

### SYMBOL_NOT_FOUND

```json
{
  "error": "SYMBOL_NOT_FOUND",
  "symbol_id": "..."
}
```

---

## 20. Configuration

POC can work with CLI flags only.

Later `.codebomb/config.yaml`:

```yaml
version: 0
repo:
  root: .
profiles:
  default: semantic
languages:
  java:
    enabled: true
    lsp:
      command: ["jdtls"]
  python:
    enabled: true
    lsp:
      command: ["pylsp"]
exclude:
  - .git/
  - node_modules/
  - target/
  - build/
  - dist/
  - .venv/
  - __pycache__/
security:
  read_only: true
  allow_outside_repo: false
```

Later optional Shiki project config can describe preferred external tool defaults without making Codebomb mandatory:

```yaml
tools:
  codebomb:
    enabled: true
    command: codebomb
    profile: semantic
    transport: stdio
```

The Shiki launcher must still work without this config by using CLI flags and PATH lookup.

---

## 21. Codex MCP Configuration Example

Once Codebomb is installed and the repo is indexed:

Preferred Shiki-mediated config:

```toml
[mcp_servers.codebomb]
command = "shiki"
args = ["tool", "codebomb", "serve", "--repo", ".", "--profile", "semantic", "--transport", "stdio"]
cwd = "."
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled = true
default_tools_approval_mode = "prompt"
```

Direct Codebomb config:

```toml
[mcp_servers.codebomb]
command = "codebomb"
args = ["serve", "--repo", ".", "--profile", "semantic", "--transport", "stdio"]
cwd = "."
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled = true
default_tools_approval_mode = "prompt"
```

Usage instruction for Codex:

```text
Use the codebomb MCP server before reading many source files.
Call codebomb.status and codebomb.build_context_pack for code context.
Do not manually scan the full repository unless Codebomb reports stale or missing index.
```

---

## 22. Shiki Integration Contract

Shiki should integrate Codebomb in two separate places:

```text
CLI launcher:
  shiki tool codebomb -> external Codebomb process

Runtime guidance:
  Shiki tasks may use Codebomb MCP tools when the server is available
```

Shiki must not implement Codebomb indexing, Codebomb storage, or Codebomb MCP tools.

### 22.1 CLI Contract

The `shiki tool codebomb` command exists for process startup and operator ergonomics:

```bash
shiki tool codebomb serve --repo . --profile semantic --transport stdio
```

It should be safe to use as an MCP server command because it does not print Shiki command banners to stdout.

Failure behavior:

```text
codebomb executable missing -> print actionable stderr message and exit non-zero
repo outside project root -> fail before starting Codebomb
Codebomb exits non-zero -> return the same exit code
```

### 22.2 Runtime Guidance

Shiki task guidance:

```md
When a Code task requires source context and Codebomb MCP is available:
1. Call `codebomb.status`.
2. If index is current, call `codebomb.build_context_pack` for the current task target.
3. Load only source slices and metadata returned by Codebomb.
4. If Codebomb is missing, stale, or blocked, report the missing code context provider instead of broad source scanning.
```

Shiki task contracts can later add optional metadata:

```yaml
code_context_provider:
  type: mcp
  server: codebomb
  tools:
    - codebomb.status
    - codebomb.build_context_pack
```

This metadata is declarative. It should not force Shiki to start an MCP server during normal `/shiki-next` execution unless a future runner explicitly owns MCP lifecycle management.

### 22.3 Adapter Guidance Later

The existing Shiki adapter installer currently writes project-local slash commands and manifests. Do not add Codebomb-specific adapter files for the first launcher PR.

Later, adapter prompts can add a small optional rule:

```text
If a configured codebomb MCP server is available, use `codebomb.build_context_pack`
before broad source scanning for code implementation, review, and fix tasks.
If the server is missing or stale, report that fact and continue only with the
bounded source files required by the active Shiki task.
```

This keeps the adapter command surface stable:

```text
/shiki-status
/shiki-next
/shiki-modify <target>
```

There is no separate `/shiki-codebomb` slash command in the POC.

---

## 23. POC Definition Of Done

The POC is complete when all of the following are true:

1. `codebomb` is installable as an independent Python package.
2. `codebomb serve --repo . --profile semantic --transport stdio` starts a read-only MCP server.
3. `codebomb index --repo . --profile semantic` produces L2 assets for Java and Python fixtures.
4. Tree-sitter extracts Java/Python symbols with file, range, signature, and hash metadata.
5. LSP semantic profile enriches Java/Python assets with definitions and references when `jdtls`/`pylsp` are available.
6. Missing LSP dependencies fail clearly in `semantic` profile.
7. MCP tools expose status, index status, file list, symbol search, symbol detail, source slice, references, and context pack.
8. MCP tools are read-only.
9. Workspace jail prevents reading outside repo root.
10. Tests cover CLI, inventory, symbol extraction, store, and context pack basics.
11. Shiki can start Codebomb through `shiki tool codebomb serve ...` without import-time dependency or stdout pollution in MCP stdio mode.

---

## 24. Risks And Mitigations

### Risk: Java LSP Setup Is Heavy

JDT LS requires Java 21 and workspace data configuration.

Mitigation:

- Keep syntax profile available.
- Make semantic dependency failure clear.
- Keep Java LSP integration small: document symbols, definitions, references first.

### Risk: Python LSP Quality Varies

`pylsp` behavior depends on project environment and plugins.

Mitigation:

- Use Tree-sitter as structural baseline.
- Use LSP facts as enrichment with `source: lsp` and confidence metadata.

### Risk: Model Trusts Stale Index

Mitigation:

- Include git commit, dirty flag, indexed_at, file hash in every result.
- `codebomb.index_status` must report stale/missing/current.

### Risk: MCP Security

Mitigation:

- Read-only tools.
- Stdio first.
- Workspace jail.
- No shell/write tools.
- No remote clone in POC.

### Risk: Overbuilding Diagrams Too Early

Mitigation:

- Defer L0 diagrams.
- Focus on L2 assets and L1 context packs first.

---

## 25. Future Work

After POC:

```text
SQLite store
watch mode
incremental indexing
call hierarchy
basic call graph
impact analysis
related-test discovery
Mermaid sequence/component diagrams
PlantUML class diagrams
Structurizr/C4 export
remote repo clone with sandbox
Shiki task-contract integration
CI summary export
review-site export
```

---

## 26. One-Sentence Product Shape

Codebomb is an independent, read-only Codebase Asset Engine that uses Tree-sitter and LSP to explode Java/Python repositories into queryable code facts, serves them through MCP, and lets Shiki or Codex load precise code context without scanning the entire repository.
