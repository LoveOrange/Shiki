"""Codex CLI Provider for Shiki's automatic track."""

from pathlib import Path

from .process import execute_process


class CodexProvider:
    """Execute each Shiki Task or Review with a fresh ``codex exec`` process."""

    name = "codex"

    def __init__(self, cwd, executable="codex", model=""):
        self.cwd = Path(cwd)
        self.executable = str(executable or "codex")
        self.model = str(model or "").strip()

    def build_command(self, read_only=False):
        command = [
            self.executable,
            "exec",
            "--ephemeral",
            "--color",
            "never",
            "--sandbox",
            "read-only" if read_only else "workspace-write",
            "--cd",
            str(self.cwd),
            "--skip-git-repo-check",
        ]
        if self.model:
            command.extend(["--model", self.model])
        command.append("-")
        return tuple(command)

    def execute_prompt(self, prompt, read_only=False):
        return execute_process(self.build_command(read_only=read_only), self.cwd, prompt)
