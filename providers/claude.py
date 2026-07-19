"""Claude Code CLI Provider for Shiki's automatic track."""

from pathlib import Path

from .process import execute_process


class ClaudeProvider:
    """Execute each Shiki Task or Review with a fresh ``claude --print`` process."""

    name = "claude"

    def __init__(self, cwd, executable="claude", model=""):
        self.cwd = Path(cwd)
        self.executable = str(executable or "claude")
        self.model = str(model or "").strip()

    def build_command(self, read_only=False):
        command = [
            self.executable,
            "--print",
            "--no-session-persistence",
            "--output-format",
            "text",
            "--permission-mode",
            "plan" if read_only else "acceptEdits",
        ]
        if self.model:
            command.extend(["--model", self.model])
        return tuple(command)

    def execute_prompt(self, prompt, read_only=False):
        return execute_process(self.build_command(read_only=read_only), self.cwd, prompt)
