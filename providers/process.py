"""Shared process boundary for the built-in CLI Providers."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class ProviderExecutionResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def execute_process(command, cwd, prompt):
    """Run one prompt in one fresh process and capture its final response."""
    command = tuple(str(part) for part in command if str(part))
    if not command:
        raise ValueError("provider command is empty")
    try:
        result = subprocess.run(
            list(command),
            cwd=str(Path(cwd)),
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return ProviderExecutionResult(
            127,
            stderr=f"provider executable not found: {command[0]}\n",
        )
    return ProviderExecutionResult(result.returncode, result.stdout or "", result.stderr or "")
