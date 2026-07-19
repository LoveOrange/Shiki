import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core-kernel"))

from _lib.context import build_context_envelope
from _lib.prompt_builder import build_execution_prompt
from _lib.task_tools import complete_task, next_task
from providers import create_provider
from providers.claude import ClaudeProvider
from providers.codex import CodexProvider
from shiki_cli.cli import provider_settings, provider_status


class V4RuntimeTests(unittest.TestCase):
    def test_status_protocol(self):
        self.assertEqual("PASS", provider_status("\nPASS: done\n"))
        self.assertEqual("CHANGE_REQUEST", provider_status("CHANGE_REQUEST: revise\n"))
        self.assertEqual("", provider_status("# heading\nPASS: too late\n"))
        task_prompt = build_execution_prompt("next")
        review_prompt = build_execution_prompt("review")
        self.assertIn("PASS, BLOCKED, FAILED, MANUAL_DECISION", task_prompt)
        task_status_line = next(line for line in task_prompt.splitlines() if "`STATUS` must be one of" in line)
        self.assertNotIn("CHANGE_REQUEST", task_status_line)
        self.assertIn("CHANGE_REQUEST", review_prompt)

    def test_context_is_deduplicated_by_content(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            feature = project / "shiki_context/features/FEAT-1"
            feature.mkdir(parents=True)
            (project / "a.md").write_text("same\n", encoding="utf-8")
            (project / "b.md").write_text("same\n", encoding="utf-8")
            envelope = build_context_envelope(
                shiki_root=ROOT,
                project_root=project,
                feature_dir=feature,
                item={"id": "T1", "target": "test evidence"},
                contract={
                    "id": "fixture",
                    "required_inputs": ["a.md", "b.md"],
                    "optional_inputs": [],
                    "workflow_ref": "core-kernel/workflows/test/run.md",
                },
                task_route="selected_item: T1",
            )
            self.assertEqual(1, len(envelope.required_artifacts))

    def test_codex_provider_uses_a_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            script = project / "codex"
            script.write_text(
                "#!/usr/bin/env python3\n"
                "import os, pathlib, sys\n"
                "pathlib.Path('pids').open('a').write(str(os.getpid()) + '\\n')\n"
                "sys.stdin.read()\n"
                "print('PASS: ok')\n",
                encoding="utf-8",
            )
            script.chmod(0o755)
            provider = CodexProvider(project, executable=script, model="gpt-test")
            self.assertEqual(0, provider.execute_prompt("one").returncode)
            self.assertEqual(0, provider.execute_prompt("two", read_only=True).returncode)
            pids = (project / "pids").read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(set(pids)))
            task_command = provider.build_command()
            review_command = provider.build_command(read_only=True)
            self.assertIn("workspace-write", task_command)
            self.assertIn("read-only", review_command)
            self.assertEqual("-", task_command[-1])
            self.assertIn("gpt-test", task_command)

    def test_claude_provider_has_isolated_task_and_review_modes(self):
        provider = ClaudeProvider(ROOT, model="sonnet")
        task_command = provider.build_command()
        review_command = provider.build_command(read_only=True)
        self.assertIn("--print", task_command)
        self.assertIn("--no-session-persistence", task_command)
        self.assertEqual("acceptEdits", task_command[task_command.index("--permission-mode") + 1])
        self.assertEqual("plan", review_command[review_command.index("--permission-mode") + 1])
        self.assertIn("sonnet", task_command)

    def test_provider_factory_accepts_only_codex_and_claude(self):
        self.assertIsInstance(create_provider("codex", ROOT), CodexProvider)
        self.assertIsInstance(create_provider("claude", ROOT), ClaudeProvider)
        with self.assertRaises(ValueError):
            create_provider("custom", ROOT)

    def test_provider_settings_load_claude_config(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "shiki.config.yaml").write_text(
                "provider:\n"
                "  name: claude\n"
                "  model: sonnet\n"
                "  executable: /opt/claude\n",
                encoding="utf-8",
            )
            self.assertEqual(
                ("claude", "/opt/claude", "sonnet"),
                provider_settings(project, ROOT, ""),
            )

    def test_task_tools_prepare_and_complete_one_row(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            feature = project / "shiki_context/features/FEAT-1"
            workspace = project / "shiki_context/workspace"
            (feature / "tests").mkdir(parents=True)
            workspace.mkdir(parents=True)
            (workspace / "active_task.md").write_text(
                "# Active Task\n\n- `stage`: Test\n- `feature`: FEAT-1\n- `next`: auto\n",
                encoding="utf-8",
            )
            (feature / "tests/test_cases.md").write_text("# Cases\n", encoding="utf-8")
            plan = feature / "_plan.md"
            plan.write_text(
                "# Feature Plan: FEAT-1\n\n## Target Outputs\n\n"
                "| id | phase | target | depends_on | contract | output_files |\n"
                "|:---|:---|:---|:---|:---|:---|\n"
                "| T1 | Test | test evidence | | `test/run.yaml` | |\n",
                encoding="utf-8",
            )
            prepared = next_task(ROOT, project, feature, scope_kind="feature")
            self.assertEqual("READY", prepared.status)
            self.assertEqual("T1", prepared.task_id)
            completion = complete_task(
                project_root=project,
                feature_dir=feature,
                task_id="T1",
                noop_reason="fixture verifier passed",
                scope_kind="feature",
            )
            self.assertEqual("PASS", completion.status)
            self.assertIn("NOOP: fixture verifier passed", plan.read_text(encoding="utf-8"))
            self.assertEqual("DONE", next_task(ROOT, project, feature, scope_kind="feature").status)


if __name__ == "__main__":
    unittest.main()
