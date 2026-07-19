"""Built-in Provider boundaries for Shiki's CLI automatic track."""

from .claude import ClaudeProvider
from .codex import CodexProvider


PROVIDER_TYPES = {
    "claude": ClaudeProvider,
    "codex": CodexProvider,
}


def create_provider(name, cwd, executable="", model=""):
    """Create one supported CLI Provider from normalized settings."""
    normalized = str(name or "codex").strip().lower()
    provider_type = PROVIDER_TYPES.get(normalized)
    if provider_type is None:
        supported = ", ".join(sorted(PROVIDER_TYPES))
        raise ValueError(f"unsupported Provider {name!r}; expected one of: {supported}")
    return provider_type(cwd=cwd, executable=executable or normalized, model=model)


__all__ = ["ClaudeProvider", "CodexProvider", "PROVIDER_TYPES", "create_provider"]
