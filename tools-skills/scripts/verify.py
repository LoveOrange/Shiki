#!/usr/bin/env python3
"""
Local verification entrypoint for Shiki framework changes.

This script creates a temporary sample project, injects a deterministic devagent
shim, and verifies the filesystem-level workflow.
"""

import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core-kernel"))
CORE_COPY_DIRS = ["docs", "core-kernel", "tools-skills", "tech-stacks", "providers", "user-interface"]
EXPECTED_CONTEXT_DIRS = [
    "shiki_context/workspace",
    "shiki_context/constitution",
    "shiki_context/project",
    "shiki_context/modules",
    "shiki_context/features",
]
EXPECTED_CONTEXT_FILES = [
    "shiki_context/project/README.md",
    "shiki_context/project/index.md",
    "shiki_context/project/_plan.md",
    "shiki_context/project/architecture.md",
    "shiki_context/project/ubiquitous_language.md",
    "shiki_context/project/techstack.md",
    "shiki_context/project/integration.md",
    "shiki_context/workspace/.gitignore",
    "shiki_context/workspace/active_task.md",
    "shiki_context/workspace/_plan.md",
    "shiki_context/constitution/tech_contracts/README.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/acl.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/exception.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/layering.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/naming.md",
    "shiki_context/constitution/tech_contracts/java/ddd-spring/persistence.md",
]
TEXT_SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    "__pycache__",
    "tmp",
}
TEXT_SKIP_FILES = set()
TEXT_SKIP_SUFFIXES = {".zip", ".pyc"}
DISALLOWED_TEXT = [
    "dry-run",
    "dry_run",
    "DRY RUN",
    "--dry",
    "batch_analysis.py",
    "Context Engineering System",
    "design_plan.md",
    "design_status.md",
    "2_module",
    "designs/*_contract.md",
    "order_contract.md",
]
PHASE_RE = re.compile(r"^## (Phase \d+: [^\n]+)(.*?)(?=^## Phase |\Z)", re.S | re.M)


def log(message: str) -> None:
    print(f"[verify] {message}")


def run(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    log("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def run_expect_fail(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    log("$ " + " ".join(cmd) + "  # expected failure")
    result = subprocess.run(cmd, cwd=str(cwd), env=env)
    if result.returncode == 0:
        raise AssertionError("Expected command to fail: " + " ".join(cmd))


def require_file(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Expected file missing: {path}")


def require_dir(path: Path) -> None:
    if not path.is_dir():
        raise AssertionError(f"Expected directory missing: {path}")


def require_workspace_ignore_policy(path: Path) -> None:
    require_file(path)
    content = path.read_text(encoding="utf-8")
    for needle in [
        "/*",
        "!/.gitignore",
        "Ignore everything created under this workspace directory.",
    ]:
        if needle not in content:
            raise AssertionError(f"{path} missing workspace ignore rule: {needle}")


def python_scripts() -> list[str]:
    files = []
    for base in [ROOT / "core-kernel" / "_lib", ROOT / "tools-skills" / "scripts"]:
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(str(path.relative_to(ROOT)))
    return files


def verify_python_and_shell() -> None:
    log("checking Python scripts")
    run([sys.executable, "-m", "py_compile", *python_scripts()])


def should_scan_text(path: Path) -> bool:
    if any(part in TEXT_SKIP_DIRS for part in path.parts):
        return False
    if path.name in TEXT_SKIP_FILES:
        return False
    if path.suffix in TEXT_SKIP_SUFFIXES:
        return False
    if path == ROOT / "tools-skills" / "scripts" / "verify.py":
        return False
    if path == ROOT / "tools-skills" / "scripts" / "simulate_scenarios.py":
        return False
    return path.is_file()


def verify_static_text() -> None:
    log("checking stale references")
    failures = []
    for path in ROOT.rglob("*"):
        if not should_scan_text(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for needle in DISALLOWED_TEXT:
            if needle in content:
                failures.append(f"{path.relative_to(ROOT)} contains {needle!r}")
    if failures:
        raise AssertionError("\n".join(failures))


def verify_core_consistency() -> None:
    log("checking core file consistency")
    cheatsheet = (ROOT / "docs" / "CHEATSHEET.md").read_text(encoding="utf-8")
    phase_contract = (ROOT / "core-kernel/runtime/phase_contract.md").read_text(encoding="utf-8")
    context_loading = (ROOT / "core-kernel/runtime/context_loading.md").read_text(encoding="utf-8")
    runner_apply = (ROOT / "core-kernel" / "workflows" / "runner" / "apply.md").read_text(encoding="utf-8")
    require_workspace_ignore_policy(ROOT / "core-kernel" / "templates" / "workspace" / ".gitignore")

    # Check CHEATSHEET has the active prompt entries
    for heading in [
        "## 1. scan",
        "## 2. new feature",
        "## 3. status",
        "## 4. apply",
        "## 5. review",
        "## 6. modify",
    ]:
        if heading not in cheatsheet:
            raise AssertionError(f"CHEATSHEET.md missing entry: {heading}")

    # No legacy headings
    for stale in ["verify last", "status check", "run next", "## 4. next"]:
        if stale in cheatsheet:
            raise AssertionError(f"CHEATSHEET.md still contains legacy heading: {stale}")

    # Check phase enum matches active_task template
    active_task = (ROOT / "core-kernel" / "templates" / "workspace" / "active_task.md").read_text(encoding="utf-8")
    contract_enum_match = re.search(r"Use this enum for the `stage` field in `active_task\.md`:\n\n```(?:text)?\n([^`]+)\n```", phase_contract)
    active_enum_match = re.search(r"`stage`: \[([^\]]+)\]", active_task)
    if contract_enum_match and active_enum_match:
        contract_enum = contract_enum_match.group(1).replace(" ", "").strip()
        active_enum = active_enum_match.group(1).replace("/", "|").replace(" ", "").strip()
        if contract_enum != active_enum:
            raise AssertionError(f"Phase enum mismatch: contract={contract_enum!r}, active_task={active_enum!r}")

    # Check all task contract YAMLs have required fields
    for contract_path in sorted((ROOT / "core-kernel" / "runtime" / "task_contracts").rglob("*.yaml")):
        from _lib.task_contracts import _load_yaml
        data = _load_yaml(contract_path.read_text(encoding="utf-8"))
        required = ["id", "stage", "kind", "goal", "workflow_ref"]
        missing = [field for field in required if field not in data]
        if missing:
            raise AssertionError(f"{contract_path.relative_to(ROOT)} missing fields: {', '.join(missing)}")

    # Check all workflow_ref resolve
    for contract_path in sorted((ROOT / "core-kernel" / "runtime" / "task_contracts").rglob("*.yaml")):
        from _lib.task_contracts import _load_yaml
        data = _load_yaml(contract_path.read_text(encoding="utf-8"))
        ref = data.get("workflow_ref", "")
        if ref and not (ROOT / ref).exists():
            raise AssertionError(f"{contract_path.relative_to(ROOT)}: workflow_ref '{ref}' does not exist")

    # Check no S-numbering in active paths
    for d in [ROOT / "core-kernel" / "workflows", ROOT / "core-kernel" / "runtime" / "task_contracts"]:
        for f in d.rglob("*"):
            if f.is_file() and re.match(r"s[0-9]", f.name):
                raise AssertionError(f"S-numbered file in active path: {f.relative_to(ROOT)}")

    # Check runtime guidance
    for needle in ["task contract", "core-kernel/runtime/task_contracts/"]:
        if needle not in context_loading + runner_apply:
            raise AssertionError(f"Missing task-contract runtime guidance: {needle}")


def copy_shiki_to(project: Path) -> None:
    shiki_dir = project / "shiki"
    shiki_dir.mkdir()
    for name in CORE_COPY_DIRS:
        src = ROOT / name
        if src.exists():
            shutil.copytree(src, shiki_dir / name)
    for name in [
        "shiki.config.yaml",
        "README.md",
    ]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, shiki_dir / name)


def write_devagent_shim(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    shim = bin_dir / "devagent"
    shim.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import re
            import sys
            from pathlib import Path

            prompt = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else ""
            ctx = Path("shiki_context")

            def write(path, content):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            if "Scan Dependencies" in prompt:
                write(ctx / "project" / "techstack.md", "# Tech Stack\\n\\n## Stack Choices\\n\\n- Spring Boot\\n")
                write(ctx / "project" / "integration.md", "# Integration\\n\\n## Data Sources\\n\\nN/A\\n")
                sys.exit(0)

            if "Entrance Analysis" in prompt:
                match = re.search(r"Module: (\\w+)", prompt)
                module = match.group(1) if match else "order"
                write(ctx / "modules" / module / "entrances" / "create_order.md", "# Entrance Spec: create_order\\n")
                write(ctx / "modules" / module / "flows" / "create_order.md", "# Flow: create_order\\n")
                sys.exit(0)

            if "Discovery Sync" in prompt:
                write(ctx / "project" / "tech_debt.md", "# Tech Debt\\n\\nN/A\\n")
                write(ctx / "project" / "integration.md", "# Integration\\n\\n## Data Sources\\n\\nN/A\\n")
                sys.exit(0)

            sys.exit(0)
            """
        ),
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)


def verify_fixture_workflow() -> None:
    log("checking fixture workflow with devagent shim")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        project = tmp / "project"
        shutil.copytree(ROOT / "tests" / "fixtures" / "java-ddd-spring-sample", project)
        copy_shiki_to(project)

        shim_bin = tmp / "bin"
        write_devagent_shim(shim_bin)
        env = os.environ.copy()
        env["PATH"] = f"{shim_bin}{os.pathsep}{env.get('PATH', '')}"

        run([sys.executable, "shiki/tools-skills/scripts/init.py"], cwd=project, env=env)
        for relative in EXPECTED_CONTEXT_DIRS:
            require_dir(project / relative)
        for relative in EXPECTED_CONTEXT_FILES:
            require_file(project / relative)
        require_workspace_ignore_policy(project / "shiki_context" / "workspace" / ".gitignore")
        if (project / "shiki_context" / "module").exists():
            raise AssertionError("init.py must not create legacy shiki_context/module/")

        # Init idempotency
        run([sys.executable, "shiki/tools-skills/scripts/init.py"], cwd=project, env=env)

        run([sys.executable, "shiki/tools-skills/scripts/scan.py", "--only", "s0.1"], cwd=project, env=env)
        run([sys.executable, "shiki/tools-skills/scripts/scan.py", "--only", "s0.2"], cwd=project, env=env)
        run([sys.executable, "shiki/tools-skills/scripts/batch_analyze.py"], cwd=project, env=env)
        for relative in [
            "shiki_context/modules/order/entrances/create_order.md",
            "shiki_context/modules/order/flows/create_order.md",
            "shiki_context/modules/order/README.md",
            "shiki_context/modules/order/index.md",
            "shiki_context/modules/order/_plan.md",
            "shiki_context/project/tech_debt.md",
        ]:
            require_file(project / relative)
        init_plan = (project / "shiki_context" / "workspace" / "_plan.md").read_text(encoding="utf-8")
        if "init.entrance" not in init_plan or "entrances/create_order.md" not in init_plan:
            raise AssertionError("scan.py must analyze entries, not only register them")
        project_index = (project / "shiki_context" / "project" / "index.md").read_text(encoding="utf-8")
        if "| `order` | `modules/order/` | `modules/order/index.md` | current |" not in project_index:
            raise AssertionError("scan.py must register discovered modules in project index.md")
        if (project / "shiki_context" / "module").exists():
            raise AssertionError("scan.py must not use legacy shiki_context/module/ as active baseline")

        # new_feature creates feature scope trio plus bootstrap lifecycle files
        run([sys.executable, "shiki/tools-skills/scripts/new_feature.py", "--taskid", "FEAT-VERIFY"], cwd=project, env=env)
        feature_dir = project / "shiki_context" / "features" / "FEAT-VERIFY"
        require_file(feature_dir / "design_brief.md")
        feature_template_root = ROOT / "core-kernel" / "templates" / "feature"
        for template_path in sorted(feature_template_root.rglob("*")):
            if template_path.is_file():
                require_file(feature_dir / template_path.relative_to(feature_template_root))

        # Verify NO legacy files created
        for should_not_exist in ["review_spec.md", "implementation_plan.md", "verification_report.md"]:
            if (feature_dir / should_not_exist).exists():
                raise AssertionError(f"new_feature.py should not create {should_not_exist}")
        if (feature_dir / "draft_specs").exists():
            raise AssertionError("new_feature.py should not create draft_specs/")
        if (feature_dir / "change_requests").exists():
            raise AssertionError("new_feature.py should not create change_requests/")
        if (feature_dir / "evidence").exists():
            raise AssertionError("new_feature.py should not create evidence/")

        brief_path = feature_dir / "design_brief.md"
        brief_text = brief_path.read_text(encoding="utf-8")
        brief_path.write_text(
            brief_text.replace(
                "**Module**: [optional; design_init may infer it]",
                "**Module**: order",
            ),
            encoding="utf-8",
        )

        plan_text = (feature_dir / "_plan.md").read_text(encoding="utf-8")
        if "| B1 | Design | design_init |" not in plan_text:
            raise AssertionError("new_feature.py must create a bootstrap plan with design_init")

        # Kernel routing: bootstrap should drive design_init
        select_bootstrap = subprocess.check_output(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'shiki/core-kernel'); "
                    "from pathlib import Path; "
                    "from _lib.kernel import select_next_item; "
                    "item, contract = select_next_item(Path('shiki_context/features/FEAT-VERIFY')); "
                    "print(item['id']); "
                    "print(contract['id'])"
                ),
            ],
            cwd=str(project),
            env=env,
            text=True,
        ).strip().splitlines()
        if select_bootstrap != ["B1", "design_init"]:
            raise AssertionError(f"bootstrap plan did not drive design_init: {select_bootstrap!r}")

        # Expand plan
        subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'shiki/core-kernel'); "
                    "from pathlib import Path; "
                    "from _lib.feature_plan import expand_plan_from_brief; "
                    "expand_plan_from_brief(Path('shiki_context/features/FEAT-VERIFY'), 'FEAT-VERIFY')"
                ),
            ],
            cwd=str(project),
            env=env,
            check=True,
        )
        plan_text = (feature_dir / "_plan.md").read_text(encoding="utf-8")
        for needle in ["| D1 | Design | model |", "| CP | Design | code_contract |", "| M1 | Merge | feature_merge |"]:
            if needle not in plan_text:
                raise AssertionError(f"expanded plan missing row: {needle}")
        feature_index_text = (feature_dir / "index.md").read_text(encoding="utf-8")
        if "| `model` | `modules.order.designs.model` | `modules/order/designs/model.md` | D1 |" not in feature_index_text:
            raise AssertionError("design_init expansion must update feature index.md")


def verify_publish_docs() -> None:
    log("checking Markdown HTML publisher")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        docs = tmp / "docs"
        site_root = tmp / "site"
        site = site_root / "web_spec"
        docs.mkdir()
        (docs / "README.md").write_text(
            textwrap.dedent(
                """\
                # Docs Home

                See [Guide](guide.md).

                | Name | Value |
                | :--- | :--- |
                | Runtime | `Shiki` |

                ```mermaid
                flowchart LR
                    A[Spec] --> B[HTML]
                ```
                """
            ),
            encoding="utf-8",
        )
        (docs / "guide.md").write_text("# Guide\n\nBack to [Home](README.md).\n", encoding="utf-8")

        run(
            [
                sys.executable,
                "tools-skills/scripts/publish_docs.py",
                str(docs),
                "--output",
                str(site_root),
                "--title",
                "Test Docs",
                "--fail-on-broken-links",
            ]
        )
        require_file(site / "index.html")
        require_file(site / "README.html")
        require_file(site / "guide.html")
        require_file(site / "publish_report.md")
        require_file(site / "assets" / "site.css")
        require_file(site / "assets" / "site.js")
        require_file(site / "assets" / "highlight.min.js")
        require_file(site / "assets" / "highlight-theme.css")
        require_file(site / "assets" / "mermaid.min.js")

        readme_html = (site / "README.html").read_text(encoding="utf-8")
        guide_html = (site / "guide.html").read_text(encoding="utf-8")
        site_js = (site / "assets" / "site.js").read_text(encoding="utf-8")
        report = (site / "publish_report.md").read_text(encoding="utf-8")
        for needle in [
            'href="guide.html"',
            "<table>",
            'class="diagram"',
            'data-diagram-action="open"',
            "diagram-viewer-stage",
            "normalizeMermaidSvg",
            "dataset.diagramWidth",
            '"inline"',
            'svg.style.maxWidth = width + "px"',
            'class="view-controls"',
            'data-layout-action="focus"',
            "specToHtmlLayout",
            "focus-mode",
            'class="nav-tree"',
            'class="toc-panel"',
            'class="toc-item toc-level-1"',
            "code-copy",
            "assets/highlight.min.js",
            "assets/mermaid.min.js",
            "Broken Markdown Links",
            "- None",
        ]:
            if needle not in readme_html + report + site_js:
                raise AssertionError(f"published docs missing expected content: {needle}")
        if 'href="README.html"' not in guide_html:
            raise AssertionError("publisher must rewrite local .md links to .html links")


def verify_git_diff_check() -> None:
    if shutil.which("git") is None:
        return
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        log("skipping git diff whitespace check outside a git repository")
        return
    log("checking git diff whitespace")
    run(["git", "diff", "--check"])


def main() -> int:
    try:
        verify_python_and_shell()
        verify_static_text()
        verify_core_consistency()
        verify_fixture_workflow()
        verify_publish_docs()
        verify_git_diff_check()
    except Exception as exc:
        print(f"[verify] FAIL: {exc}", file=sys.stderr)
        return 1
    log("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
